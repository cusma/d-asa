from pathlib import Path
from textwrap import dedent

import pytest

from smart_contracts.mixin_composition import (
    CompositionValidationError,
    validate_contract_composition,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SMART_CONTRACTS_ROOT = REPO_ROOT / "smart_contracts"


def _validate_source(tmp_path: Path, source: str) -> None:
    scratch_dir = SMART_CONTRACTS_ROOT / "_tmp_mixin_guards"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    source_path = scratch_dir / f"tmp_{tmp_path.name.replace('-', '_')}.py"
    source_path.write_text(dedent(source), encoding="utf-8")
    try:
        validate_contract_composition(source_path, SMART_CONTRACTS_ROOT)
    finally:
        source_path.unlink(missing_ok=True)
        # Remove directory if empty
        try:
            scratch_dir.rmdir()
        except OSError:
            pass


def test_pass_existing_fixed_coupon_contract() -> None:
    validate_contract_composition(
        SMART_CONTRACTS_ROOT / "fixed_coupon_bond" / "contract.py",
        SMART_CONTRACTS_ROOT,
    )


def test_fail_coupon_transfer_without_coupon_cashflow(tmp_path: Path) -> None:
    with pytest.raises(
        CompositionValidationError, match="core_prepare_transfer_with_coupon"
    ):
        _validate_source(
            tmp_path,
            """
            from modules.transfer_agent import CouponTransferAgentMixin


            class BrokenCouponTransfer(CouponTransferAgentMixin):
                pass
            """,
        )


def test_fail_coupon_transfer_wrong_mro_default_wins(tmp_path: Path) -> None:
    with pytest.raises(
        CompositionValidationError, match="core_prepare_transfer_with_coupon"
    ):
        _validate_source(
            tmp_path,
            """
            from modules.core_financial import FixedCouponCashflowMixin
            from modules.transfer_agent import CouponTransferAgentMixin


            class WrongOrderCouponTransfer(
                CouponTransferAgentMixin,
                FixedCouponCashflowMixin,
            ):
                pass
            """,
        )


def test_fail_coupon_payment_without_coupon_cashflow(tmp_path: Path) -> None:
    with pytest.raises(CompositionValidationError, match="core_prepare_coupon_payment"):
        _validate_source(
            tmp_path,
            """
            from modules.payment_agent import CouponPaymentAgentMixin


            class BrokenCouponPayment(CouponPaymentAgentMixin):
                pass
            """,
        )


def test_fail_coupon_counting_hook_not_overridden(tmp_path: Path) -> None:
    with pytest.raises(CompositionValidationError, match="count_due_coupons"):
        _validate_source(
            tmp_path,
            """
            from modules.core_financial import CouponCashflowMixin
            from modules.payment_agent import CouponPaymentAgentMixin


            class BrokenCouponCounting(CouponCashflowMixin, CouponPaymentAgentMixin):
                pass
            """,
        )


def test_fail_principal_payment_without_cashflow_provider(tmp_path: Path) -> None:
    with pytest.raises(
        CompositionValidationError, match="core_prepare_principal_payment"
    ):
        _validate_source(
            tmp_path,
            """
            from modules.payment_agent import PrincipalPaymentAgentMixin


            class BrokenPrincipalPayment(PrincipalPaymentAgentMixin):
                pass
            """,
        )


def test_fail_principal_authorization_hook_not_overridden(tmp_path: Path) -> None:
    with pytest.raises(
        CompositionValidationError, match="assert_pay_principal_authorization"
    ):
        _validate_source(
            tmp_path,
            """
            from modules.core_financial import NoCouponCashflowMixin
            from modules.payment_agent import PrincipalPaymentAgentMixin


            class BrokenPrincipalAuthorization(
                NoCouponCashflowMixin,
                PrincipalPaymentAgentMixin,
            ):
                pass
            """,
        )
