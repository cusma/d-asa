"""Core normalization logic for ACTUS contracts."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from smart_contracts import constants as cst

from ..contracts import ContractAttributes
from ..day_count import year_fraction_fixed
from ..errors import ActusNormalizationError, UnsupportedActusFeatureError
from ..models import (
    ExecutionScheduleEntry,
    InitialKernelState,
    NormalizationResult,
    NormalizedActusTerms,
    ObservedEventRequest,
)
from ..registry import ALLOWED_EVENT_TYPES, CONTRACT_TYPE_IDS
from ..unix_time import UTCTimeStamp
from .ann_builder import build_ann_schedule
from .builders import (
    build_clm_schedule,
    build_ied_seed,
    build_lam_schedule,
    build_lax_schedule,
    build_nam_schedule,
    build_pam_schedule,
)
from .conversions import compute_initial_exchange_amount, rate_to_fp, to_asa_units
from .event_seeds import EventSeed, get_seed_sort_key, seed_from_preprocessed


def _coerce_schedule_int(value: int | float | Decimal) -> int:
    """Coerce pre-normalized schedule payload values to concrete ints."""
    return int(value)


def extract_base_contract_type(contract_type: str) -> str:
    """
    Extract the base contract type from a potentially subtyped contract type string.

    The type:subtype notation allows contracts to specify variants (e.g., "ANN:ZCB").
    This function extracts the base type for validation and logic that should apply
    to all subtypes of a given base type.

    Args:
        contract_type: Contract type string, possibly with subtype (e.g., "ANN:ZCB")

    Returns:
        Base contract type without subtype (e.g., "ANN" from "ANN:ZCB")

    Example:
        >>> extract_base_contract_type("ANN:ZCB")
        'ANN'
        >>> extract_base_contract_type("PAM")
        'PAM'
    """
    return contract_type.split(":")[0] if ":" in contract_type else contract_type


def get_initial_next_principal_redemption(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> int:
    """
    Resolve the initial next principal redemption for the first IED state.

    For ANN contracts (including subtypes like "ANN:ZCB"), calculates the annuity payment amount.
    For other contracts, uses the configured next_principal_redemption_amount.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Initial principal redemption amount in ASA base units.
    """
    from .annuity import resolve_annuity_payment

    base_type = extract_base_contract_type(contract.contract_type)
    if base_type != "ANN":
        if contract.next_principal_redemption_amount is None:
            return 0
        return to_asa_units(contract.next_principal_redemption_amount, asa_decimals)
    return resolve_annuity_payment(contract, terms, asa_decimals)


def normalize_contract_attributes(
    contract: ContractAttributes,
    *,
    denomination_asset_id: int,
    denomination_asset_decimals: int,
    notional_unit_value: int | float | Decimal,
    secondary_market_opening_date: UTCTimeStamp,
    secondary_market_closure_date: UTCTimeStamp,
    preprocessed_events: (
        Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None
    ) = None,
) -> NormalizationResult:
    """
    Normalize ACTUS contract attributes into AVM-compatible terms, schedule, and state.

    Transforms human-readable ACTUS contract parameters into fixed-point integers,
    generates the execution schedule, and initializes the contract kernel state.

    Args:
        contract: ACTUS contract attributes with dates, amounts, and cycles.
        denomination_asset_id: ASA ID for the denomination asset.
        denomination_asset_decimals: Decimal places for the denomination ASA.
        notional_unit_value: Notional value per unit in denomination ASA.
        secondary_market_opening_date: Unix timestamp for secondary market opening.
        secondary_market_closure_date: Unix timestamp for secondary market closure.
        preprocessed_events: Optional pre-generated event schedule.

    Returns:
        NormalizationResult containing normalized terms, execution schedule, and initial state.

    Raises:
        ActusNormalizationError: If status_date >= initial_exchange_date or invalid config.

    Example:
        >>> contract = ContractAttributes(
        ...     contract_type="PAM",
        ...     status_date=1609459200,  # 2021-01-01
        ...     initial_exchange_date=1612137600,  # 2021-02-01
        ...     maturity_date=1643673600,  # 2022-02-01
        ...     notional_principal=100000,
        ...     nominal_interest_rate=0.05,
        ... )
        >>> result = normalize_contract_attributes(
        ...     contract,
        ...     denomination_asset_id=1,
        ...     denomination_asset_decimals=6,
        ...     notional_unit_value=100,
        ... )
    """
    if contract.status_date >= contract.initial_exchange_date:
        raise ActusNormalizationError(
            "D-ASA requires status_date to be strictly before initial_exchange_date"
        )

    # Extract base contract type (e.g., "PAM" from "PAM:ZCB")
    base_contract_type = extract_base_contract_type(contract.contract_type)

    pdied_asa = compute_initial_exchange_amount(
        contract.notional_principal,
        contract.premium_discount_at_ied,
        denomination_asset_decimals,
    )

    # Normalize ACTUS contract terms to AVM
    terms = NormalizedActusTerms(
        # Contract
        contract_id=contract.contract_id,
        contract_type=CONTRACT_TYPE_IDS[base_contract_type],
        # Denomination
        denomination_asset_id=denomination_asset_id,
        # Time
        initial_exchange_date=contract.initial_exchange_date,
        maturity_date=contract.maturity_date,
        secondary_market_opening_date=secondary_market_opening_date,
        secondary_market_closure_date=secondary_market_closure_date,
        # Principal
        notional_principal=to_asa_units(
            contract.notional_principal, denomination_asset_decimals
        ),
        notional_unit_value=to_asa_units(
            notional_unit_value, denomination_asset_decimals
        ),
        initial_exchange_amount=pdied_asa,
        next_principal_redemption_amount=to_asa_units(
            contract.next_principal_redemption_amount, denomination_asset_decimals
        ),
        # Interest
        rate_reset_spread=rate_to_fp(contract.rate_reset_spread),
        rate_reset_multiplier=rate_to_fp(contract.rate_reset_multiplier),
        rate_reset_floor=rate_to_fp(contract.rate_reset_floor),
        rate_reset_cap=rate_to_fp(contract.rate_reset_cap),
        rate_reset_next=rate_to_fp(
            contract.rate_reset_next
            if contract.rate_reset_next is not None
            else contract.nominal_interest_rate
        ),
        # Day Count Convention
        day_count_convention=contract.day_count_convention,
        # Scaling
        fixed_point_scale=cst.FIXED_POINT_SCALE,
    )

    # Normalize ACTUS contract schedule to AVM
    schedule = build_schedule(
        contract,
        terms=terms,
        preprocessed_events=preprocessed_events,
        contract_type=contract.contract_type,
        status_date=contract.status_date,
        asa_decimals=denomination_asset_decimals,
    )

    # Normalize ACTUS contract initial state to AVM
    initial_state = InitialKernelState(
        status_date=contract.status_date,
        event_cursor=0,
        outstanding_principal=0,
        interest_calculation_base=0,
        nominal_interest_rate=0,
        accrued_interest=0,
        next_principal_redemption=0,
        cumulative_interest_index=0,
        cumulative_principal_index=0,
    )
    return NormalizationResult(
        terms=terms,
        schedule=schedule,
        initial_state=initial_state,
    )


def build_schedule(
    contract: ContractAttributes,
    *,
    terms: NormalizedActusTerms,
    preprocessed_events: Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None,
    contract_type: str,
    status_date: int,
    asa_decimals: int,
) -> tuple[ExecutionScheduleEntry, ...]:
    """
    Build the final execution schedule from event seeds or preprocessed events.

    Converts intermediate event seeds into fully populated ExecutionScheduleEntry
    objects with computed accrual factors and proper event ordering.

    Args:
        contract: Original ACTUS contract attributes.
        terms: Normalized contract terms.
        preprocessed_events: Optional pre-generated event schedule.
        contract_type: Base contract type (e.g., "PAM", "LAM").
        status_date: Contract status date (must precede all events).
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Sorted tuple of ExecutionScheduleEntry objects.

    Raises:
        UnsupportedActusFeatureError: If event type not allowed for contract type.
        ActusNormalizationError: If events not in chronological order.
    """
    # Extract base contract type
    base_contract_type = extract_base_contract_type(contract_type)

    if preprocessed_events is not None:
        seeds = [
            seed_from_preprocessed(index, item)
            for index, item in enumerate(preprocessed_events)
        ]
    else:
        seeds = list(
            build_schedule_seeds(
                contract,
                terms,
                contract_type=base_contract_type,
                asa_decimals=asa_decimals,
            )
        )

    if not any(seed.event_type == "IED" for seed in seeds):
        seeds.append(build_ied_seed(contract, terms, asa_decimals=asa_decimals))

    ordered = sorted(seeds, key=get_seed_sort_key)
    allowed = ALLOWED_EVENT_TYPES[base_contract_type]
    entries: list[ExecutionScheduleEntry] = []
    previous_ts = status_date
    for event_id, seed in enumerate(ordered):
        if seed.event_type not in allowed:
            raise UnsupportedActusFeatureError(
                f"Unsupported event {seed.event_type} for {base_contract_type}"
            )
        if seed.event_type != "IED" and seed.scheduled_time < previous_ts:
            raise ActusNormalizationError(
                "ACTUS scheduled_time must be non-decreasing in event execution order"
            )
        accrual_factor = seed.accrual_factor
        if accrual_factor is None:
            if seed.event_type == "IED":
                accrual_factor = 0
            else:
                accrual_factor = year_fraction_fixed(
                    previous_ts,
                    seed.scheduled_time,
                    day_count_convention=terms.day_count_convention,
                    maturity_date=terms.maturity_date,
                )
        redemption_accrual_factor = seed.redemption_accrual_factor
        if redemption_accrual_factor is None:
            if seed.redemption_accrual_end > seed.redemption_accrual_start:
                redemption_accrual_factor = year_fraction_fixed(
                    seed.redemption_accrual_start,
                    seed.redemption_accrual_end,
                    day_count_convention=terms.day_count_convention,
                    maturity_date=terms.maturity_date,
                )
            else:
                redemption_accrual_factor = 0
        entries.append(
            ExecutionScheduleEntry(
                event_id=event_id,
                event_type=seed.event_type,
                scheduled_time=seed.scheduled_time,
                accrual_factor=_coerce_schedule_int(accrual_factor),
                redemption_accrual_factor=_coerce_schedule_int(
                    redemption_accrual_factor
                ),
                next_nominal_interest_rate=_coerce_schedule_int(
                    seed.next_nominal_interest_rate
                ),
                next_principal_redemption=seed.next_principal_redemption,
                next_outstanding_principal=seed.next_outstanding_principal,
                flags=seed.flags,
            )
        )
        previous_ts = seed.scheduled_time
    return tuple(entries)


def build_schedule_seeds(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    *,
    contract_type: str,
    asa_decimals: int,
) -> tuple[EventSeed, ...]:
    """
    Dispatch contract-type-specific schedule construction.

    Routes to the appropriate schedule builder based on contract type
    (PAM, LAM, NAM, ANN, LAX, or CLM).

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        contract_type: Base contract type (without subtype).
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the contract's execution schedule.
    """
    if contract_type == "PAM":
        return build_pam_schedule(contract, terms)
    if contract_type == "CLM":
        return build_clm_schedule(contract, terms)
    if contract_type == "LAM":
        return build_lam_schedule(contract, terms, asa_decimals)
    if contract_type == "NAM":
        return build_nam_schedule(contract, terms, asa_decimals)
    if contract_type == "ANN":
        return build_ann_schedule(contract, terms, asa_decimals)
    if contract_type == "LAX":
        return build_lax_schedule(contract, terms, asa_decimals)
    raise ActusNormalizationError(f"Unsupported ACTUS contract type: {contract_type}")
