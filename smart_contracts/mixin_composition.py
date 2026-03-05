import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClassInfo:
    fqcn: str
    module: str
    name: str
    bases: tuple[str, ...]
    methods: frozenset[str]
    path: Path


class CompositionValidationError(ValueError):
    pass


_SAFETY_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "modules.transfer_agent.coupon.CouponTransferAgentMixin",
        ("core_prepare_transfer_with_coupon",),
        "modules.transfer_agent.common.TransferAgentCommonMixin",
    ),
    (
        "modules.transfer_agent.no_coupon.NoCouponTransferAgentMixin",
        ("core_prepare_transfer_no_coupon",),
        "modules.transfer_agent.common.TransferAgentCommonMixin",
    ),
    (
        "modules.payment_agent.coupon.CouponPaymentAgentMixin",
        ("core_prepare_coupon_payment", "core_apply_coupon_payment"),
        "modules.payment_agent.common.PaymentAgentCommonMixin",
    ),
    (
        "modules.payment_agent.principal.PrincipalPaymentAgentMixin",
        ("core_prepare_principal_payment", "core_apply_principal_payment"),
        "modules.payment_agent.common.PaymentAgentCommonMixin",
    ),
    (
        "modules.transfer_agent.coupon.CouponTransferAgentMixin",
        ("count_due_coupons", "all_due_coupons_paid"),
        "modules.core_financial.common.CoreFinancialCommonMixin",
    ),
    (
        "modules.payment_agent.coupon.CouponPaymentAgentMixin",
        ("count_due_coupons", "all_due_coupons_paid"),
        "modules.core_financial.common.CoreFinancialCommonMixin",
    ),
    (
        "modules.payment_agent.principal.PrincipalPaymentAgentMixin",
        ("assert_pay_principal_authorization",),
        "modules.core_financial.common.CoreFinancialCommonMixin",
    ),
)


def validate_contract_composition(contract_path: Path, source_root: Path) -> None:
    class_map, alias_map = _index_classes(_resolve_source_roots(source_root))
    normalized_contract_path = contract_path.resolve()
    target_classes = [
        info
        for info in class_map.values()
        if info.path.resolve() == normalized_contract_path
        and not info.name.endswith("Mixin")
    ]
    if not target_classes:
        raise CompositionValidationError(
            f"No concrete contract class found in {contract_path}"
        )

    errors: list[str] = []
    mro_cache: dict[str, tuple[str, ...]] = {}
    for target in target_classes:
        errors.extend(_validate_class(target.fqcn, class_map, alias_map, mro_cache))

    if errors:
        raise CompositionValidationError("\n".join(errors))


def _validate_class(
    contract_fqcn: str,
    class_map: dict[str, ClassInfo],
    alias_map: dict[str, str],
    mro_cache: dict[str, tuple[str, ...]],
) -> list[str]:
    mro = _linearize(contract_fqcn, class_map, alias_map, mro_cache, set())
    mro_set = set(mro)
    errors: list[str] = []

    for agent_mixin, hooks, forbidden_owner in _SAFETY_RULES:
        if agent_mixin not in mro_set:
            continue
        for hook in hooks:
            owner = _resolve_hook_owner(hook, mro, class_map)
            if owner is None:
                errors.append(
                    f"Invalid mixin composition for {contract_fqcn}: hook '{hook}' "
                    "could not be resolved in MRO. Include the appropriate cashflow "
                    "mixin before agent mixins or provide an explicit safe override."
                )
                continue
            if owner == forbidden_owner:
                errors.append(
                    f"Invalid mixin composition for {contract_fqcn}: hook '{hook}' "
                    f"resolves to unsafe default '{owner}'. Include the appropriate "
                    "cashflow mixin before agent mixins or provide an explicit safe "
                    "override."
                )

    return errors


def _resolve_hook_owner(
    hook_name: str, mro: tuple[str, ...], class_map: dict[str, ClassInfo]
) -> str | None:
    for class_fqcn in mro:
        class_info = class_map.get(class_fqcn)
        if class_info and hook_name in class_info.methods:
            return class_fqcn
    return None


def _linearize(
    class_fqcn: str,
    class_map: dict[str, ClassInfo],
    alias_map: dict[str, str],
    mro_cache: dict[str, tuple[str, ...]],
    active_stack: set[str],
) -> tuple[str, ...]:
    class_fqcn = _canonicalize_fqcn(class_fqcn, alias_map)
    if class_fqcn in mro_cache:
        return mro_cache[class_fqcn]
    if class_fqcn in active_stack:
        raise CompositionValidationError(
            f"Cyclic inheritance detected while resolving MRO for {class_fqcn}"
        )

    class_info = class_map.get(class_fqcn)
    if class_info is None:
        mro_cache[class_fqcn] = (class_fqcn,)
        return mro_cache[class_fqcn]

    active_stack.add(class_fqcn)
    bases = [_canonicalize_fqcn(base, alias_map) for base in class_info.bases]
    merged_bases = _c3_merge(
        [
            list(_linearize(base, class_map, alias_map, mro_cache, active_stack))
            for base in bases
        ]
        + [bases.copy()]
    )
    active_stack.remove(class_fqcn)

    mro_cache[class_fqcn] = (class_fqcn, *merged_bases)
    return mro_cache[class_fqcn]


def _c3_merge(sequences: list[list[str]]) -> tuple[str, ...]:
    result: list[str] = []
    work = [seq.copy() for seq in sequences if seq]
    while work:
        candidate = None
        for seq in work:
            head = seq[0]
            if all(head not in other[1:] for other in work):
                candidate = head
                break
        if candidate is None:
            raise CompositionValidationError("Cannot resolve class MRO with C3 merge")

        result.append(candidate)
        next_work: list[list[str]] = []
        for seq in work:
            if seq and seq[0] == candidate:
                seq = seq[1:]
            if seq:
                next_work.append(seq)
        work = next_work

    return tuple(result)


def _resolve_source_roots(source_root: Path) -> tuple[Path, ...]:
    """
    Build source roots for composition indexing.

    Contracts live under `smart_contracts/`, while shared mixins now live in the
    sibling top-level `modules/` package.
    """
    resolved_source_root = source_root.resolve()
    source_roots: list[Path] = [resolved_source_root]

    sibling_modules_root = resolved_source_root.parent / "modules"
    if (
        sibling_modules_root.is_dir()
        and (sibling_modules_root / "__init__.py").exists()
    ):
        source_roots.append(sibling_modules_root.resolve())

    deduped_roots: list[Path] = []
    seen_roots: set[Path] = set()
    for root in source_roots:
        if root in seen_roots:
            continue
        seen_roots.add(root)
        deduped_roots.append(root)
    return tuple(deduped_roots)


def _index_classes(
    source_roots: tuple[Path, ...],
) -> tuple[dict[str, ClassInfo], dict[str, str]]:
    class_map: dict[str, ClassInfo] = {}
    alias_map: dict[str, str] = {}
    for source_root in source_roots:
        for source_file in source_root.rglob("*.py"):
            if "artifacts" in source_file.parts:
                continue

            module_name = _module_name_from_path(source_file, source_root)
            source_ast = ast.parse(source_file.read_text(encoding="utf-8"))
            module_class_names = {
                node.name for node in source_ast.body if isinstance(node, ast.ClassDef)
            }
            import_map = _build_import_map(
                source_ast, module_name, is_package=source_file.name == "__init__.py"
            )
            for local_name, target_name in import_map.items():
                alias_map[f"{module_name}.{local_name}"] = target_name

            for node in source_ast.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                base_names = tuple(
                    _resolve_base_name(
                        base, module_name, import_map, module_class_names
                    )
                    for base in node.bases
                )
                methods = frozenset(
                    child.name
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                fqcn = f"{module_name}.{node.name}"
                class_map[fqcn] = ClassInfo(
                    fqcn=fqcn,
                    module=module_name,
                    name=node.name,
                    bases=base_names,
                    methods=methods,
                    path=source_file,
                )
    return class_map, alias_map


def _build_import_map(
    module_ast: ast.Module, module_name: str, *, is_package: bool
) -> dict[str, str]:
    import_map: dict[str, str] = {}
    for node in module_ast.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".")[0]
                import_map[local_name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module is None and node.level == 0:
                continue
            absolute_module = _resolve_import_module(
                module_name, node.module, node.level, is_package=is_package
            )
            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname or alias.name
                import_map[local_name] = f"{absolute_module}.{alias.name}"
    return import_map


def _resolve_base_name(
    base: ast.expr,
    module_name: str,
    import_map: dict[str, str],
    module_class_names: set[str],
) -> str:
    if isinstance(base, ast.Name):
        if base.id in import_map:
            return import_map[base.id]
        if base.id in module_class_names:
            return f"{module_name}.{base.id}"
        return base.id

    dotted = _dotted_name(base)
    if dotted is None:
        return ast.unparse(base)

    root, _, remainder = dotted.partition(".")
    if root in import_map:
        imported = import_map[root]
        return imported if not remainder else f"{imported}.{remainder}"
    if root in module_class_names:
        return f"{module_name}.{dotted}"
    return dotted


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        if base is None:
            return None
        return f"{base}.{node.attr}"
    return None


def _module_name_from_path(path: Path, source_root: Path) -> str:
    parts = list(path.relative_to(source_root.parent).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_import_module(
    module_name: str, imported_module: str | None, level: int, *, is_package: bool
) -> str:
    if level == 0:
        if imported_module is None:
            return module_name
        return imported_module

    package_parts = module_name.split(".")
    if not is_package:
        package_parts = package_parts[:-1]
    if level > len(package_parts):
        raise CompositionValidationError(
            f"Invalid relative import level {level} in module {module_name}"
        )
    prefix = package_parts[: len(package_parts) - (level - 1)]
    if imported_module:
        return ".".join((*prefix, imported_module))
    return ".".join(prefix)


def _canonicalize_fqcn(fqcn: str, alias_map: dict[str, str]) -> str:
    resolved = fqcn
    seen: set[str] = set()
    while resolved in alias_map and resolved not in seen:
        seen.add(resolved)
        resolved = alias_map[resolved]
    return resolved
