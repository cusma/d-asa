"""ACTUS Contract normalization to AVM"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from smart_contracts import constants as cst
from smart_contracts import enums

from .contracts import ContractAttributes
from .day_count import days_in_month, year_fraction_fixed
from .errors import ActusNormalizationError, UnsupportedActusFeatureError
from .models import (
    ExecutionScheduleEntry,
    InitialKernelState,
    NormalizationResult,
    NormalizedActusTerms,
    ObservedEventRequest,
)
from .registry import (
    ALLOWED_EVENT_TYPES,
    CONTRACT_TYPE_IDS,
    EVENT_SCHEDULE_PRIORITY,
)
from .schedule import (
    Cycle,
    datetime_to_timestamp,
    resolve_array_schedule,
    resolve_cycle_schedule,
    timestamp_to_datetime,
)
from .unix_time import UTCTimeStamp


def _to_asa_units(amount: int | float | Decimal, asa_decimals: int) -> int:
    """
    Convert a decimal amount to ASA base units (uint64).

    Scales the amount by 10^asa_decimals to represent fractional values as integers.

    Example:
        >>> _to_asa_units(100.42, 3)  # 100.42 with 3 decimals
        100420
        >>> _to_asa_units(100, 2)  # 100 with 2 decimals
        10000

    Args:
        amount: The numeric value to convert.
        asa_decimals: Number of decimal places for the ASA.

    Returns:
        The amount in ASA base units as an integer.

    Raises:
        TypeError: If value is not int, float, or Decimal.
        ActusNormalizationError: If result exceeds uint64 bounds.
    """

    if isinstance(amount, (int, float, Decimal)):
        scale = 10**asa_decimals
        result = int(Decimal(str(amount)) * scale)
    else:
        raise TypeError(f"Unsupported value type: {type(amount)}")

    if result < 0 or result > cst.MAX_UINT64:
        raise ActusNormalizationError(
            f"Value {amount} results in {result} which exceeds uint64 bounds"
        )

    return result


def _rate_to_fp(value: int | float | Decimal) -> int:
    """
    Convert decimal rates to fixed-point integer representation.

    Scales decimal rates by FIXED_POINT_SCALE for AVM-compatible uint64 storage.

    Example:
        >>> _rate_to_fp(0.05)  # 5% rate with FIXED_POINT_SCALE=1_000_000_000
        50000000

    Args:
        value: The rate value (e.g., 0.05 for 5%).

    Returns:
        Fixed-point scaled rate as uint64 integer.

    Raises:
        TypeError: If value is not int, float, or Decimal.
        ActusNormalizationError: If result exceeds uint64 bounds.
    """

    if isinstance(value, (int, float, Decimal)):
        result = int(Decimal(str(value)) * cst.FIXED_POINT_SCALE)
    else:
        raise TypeError(f"Unsupported value type: {type(value)}")

    if result < 0 or result > cst.MAX_UINT64:
        raise ActusNormalizationError(
            f"Value {value} results in {result} which exceeds uint64 bounds"
        )

    return result


def _compute_initial_exchange_amount(
    notional: int | float | Decimal,
    premium_discount_at_ied: int | float | Decimal,
    asa_decimals: int,
) -> int:
    """
    Calculate the initial exchange amount adjusted for premium/discount.

    Returns the net notional after subtracting any premium/discount at IED
    (Initial Exchange Date).

    Args:
        notional: The notional principal amount.
        premium_discount_at_ied: Premium/discount adjustment at IED.
            Positive value = discount (reduces notional)
            Negative value = premium (increases notional)
        asa_decimals: Number of decimal places for the ASA.

    Returns:
        Net initial exchange amount in ASA base units.
    """
    notional = _to_asa_units(notional, asa_decimals)

    # Handle premium (negative) and discount (positive) separately
    # to avoid _to_asa_units rejecting negative values
    if premium_discount_at_ied >= 0:
        pdied = _to_asa_units(premium_discount_at_ied, asa_decimals)
        return notional - pdied
    else:
        # For negative premium_discount (premium), convert absolute value and add
        pdied = _to_asa_units(-premium_discount_at_ied, asa_decimals)
        return notional + pdied


def _deduplicate_timestamps(ts: Sequence[UTCTimeStamp]) -> tuple[UTCTimeStamp, ...]:
    """Remove duplicate timestamps while preserving sorted schedule order."""
    return tuple(dict.fromkeys(sorted(ts)))


@dataclass(frozen=True, slots=True)
class _EventSeed:
    """
    Intermediate normalized event before final schedule encoding.

    Represents a scheduled event during the normalization process, containing
    all necessary information to generate the final ExecutionScheduleEntry.

    Attributes:
        event_type: ACTUS event type (e.g., "IED", "IP", "PR", "MD").
        scheduled_time: Unix timestamp when event occurs.
        accrual_factor: Optional year fraction for interest accrual.
        redemption_accrual_factor: Optional year fraction for redemption accrual.
        redemption_accrual_start: Start timestamp for redemption accrual period.
        redemption_accrual_end: End timestamp for redemption accrual period.
        next_nominal_interest_rate: Interest rate after this event.
        next_principal_redemption: Principal redemption amount.
        next_outstanding_principal: Outstanding principal after this event.
        flags: Event flags (cash/non-cash, etc.).
    """

    event_type: str
    scheduled_time: UTCTimeStamp
    accrual_factor: int | float | Decimal | None = None
    redemption_accrual_factor: int | float | Decimal | None = None
    redemption_accrual_start: int = 0
    redemption_accrual_end: int = 0
    next_nominal_interest_rate: int | float | Decimal = 0
    next_principal_redemption: int = 0
    next_outstanding_principal: int = 0
    flags: int = 0


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
    base_contract_type = (
        contract.contract_type.split(":")[0]
        if ":" in contract.contract_type
        else contract.contract_type
    )

    pdied_asa = _compute_initial_exchange_amount(
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
        notional_principal=_to_asa_units(
            contract.notional_principal, denomination_asset_decimals
        ),
        notional_unit_value=_to_asa_units(
            notional_unit_value, denomination_asset_decimals
        ),
        initial_exchange_amount=pdied_asa,
        next_principal_redemption_amount=_to_asa_units(
            contract.next_principal_redemption_amount, denomination_asset_decimals
        ),
        # Interest
        rate_reset_spread=_rate_to_fp(contract.rate_reset_spread),
        rate_reset_multiplier=_rate_to_fp(contract.rate_reset_multiplier),
        rate_reset_floor=_rate_to_fp(contract.rate_reset_floor),
        rate_reset_cap=_rate_to_fp(contract.rate_reset_cap),
        rate_reset_next=_rate_to_fp(
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
    schedule = _normalize_schedule(
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


def _normalize_schedule(
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
    base_contract_type = (
        contract_type.split(":")[0] if ":" in contract_type else contract_type
    )

    if preprocessed_events is not None:
        seeds = [
            _seed_from_preprocessed(index, item)
            for index, item in enumerate(preprocessed_events)
        ]
    else:
        seeds = list(
            _build_schedule_seeds(
                contract,
                terms,
                contract_type=base_contract_type,
                asa_decimals=asa_decimals,
            )
        )

    if not any(seed.event_type == "IED" for seed in seeds):
        seeds.append(_initial_exchange_seed(contract, terms, asa_decimals=asa_decimals))

    ordered = sorted(seeds, key=_seed_sort_key)
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
                accrual_factor=accrual_factor,
                redemption_accrual_factor=redemption_accrual_factor,
                next_nominal_interest_rate=seed.next_nominal_interest_rate,
                next_principal_redemption=seed.next_principal_redemption,
                next_outstanding_principal=seed.next_outstanding_principal,
                flags=seed.flags,
            )
        )
        previous_ts = seed.scheduled_time
    return tuple(entries)


def _build_schedule_seeds(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    *,
    contract_type: str,
    asa_decimals: int,
) -> tuple[_EventSeed, ...]:
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
    # PAM and CLM don't require asa_decimals
    if contract_type in ("PAM", "CLM"):
        dispatch = {
            "PAM": _build_pam_schedule,
            "CLM": _build_clm_schedule,
        }
        return dispatch[contract_type](contract, terms)

    # Other contract types require asa_decimals
    dispatch = {
        "LAM": _build_lam_schedule,
        "NAM": _build_nam_schedule,
        "ANN": _build_ann_schedule,
        "LAX": _build_lax_schedule,
    }
    return dispatch[contract_type](contract, terms, asa_decimals)


def _initial_exchange_seed(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> _EventSeed:
    """
    Build the mandatory initial exchange event seed.

    Creates the IED (Initial Exchange Date) event that establishes the initial
    contract state including principal and interest rate.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Event seed for the IED event.
    """

    return _EventSeed(
        event_type="IED",
        scheduled_time=terms.initial_exchange_date,
        next_nominal_interest_rate=_rate_to_fp(contract.nominal_interest_rate),
        next_principal_redemption=_initial_next_principal_redemption(
            contract, terms, asa_decimals
        ),
        next_outstanding_principal=terms.notional_principal,
        flags=enums.FLAG_NON_CASH_EVENT,
    )


def _build_pam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms
) -> tuple[_EventSeed, ...]:
    """
    Build the normalized PAM (Principal at Maturity) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.

    Returns:
        Tuple of event seeds for the PAM schedule.

    Raises:
        ActusNormalizationError: If maturity_date is not specified.
    """

    if terms.maturity_date is None:
        raise ActusNormalizationError("PAM normalization requires maturity_date")

    seeds: list[_EventSeed] = []
    outstanding = terms.notional_principal
    for ts in _interest_schedule(contract, terms):
        seeds.append(
            _seed_from_timestamp(
                ts,
                event_type="IP",
                next_outstanding_principal=outstanding,
                flags=enums.FLAG_CASH_EVENT,
            )
        )
    seeds.extend(_rate_reset_schedule(contract, outstanding, terms.maturity_date))
    seeds.append(
        _seed_from_timestamp(
            terms.maturity_date,
            event_type="MD",
            next_outstanding_principal=0,
            flags=enums.FLAG_CASH_EVENT,
        )
    )
    return tuple(seeds)


def _build_lam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """
    Build the normalized LAM (Linear Amortizer) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the LAM schedule.
    """
    return _build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=False, lax=False
    )


def _build_nam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """
    Build the normalized NAM (Negative Amortizer) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the NAM schedule.
    """
    return _build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=True, lax=False
    )


def _build_ann_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """
    Build the normalized ANN (Annuity) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the ANN schedule.
    """
    return _build_annuity_schedule(contract, terms, asa_decimals)


def _build_lax_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """
    Build the normalized LAX (Linear Amortizer with eXtensions) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the LAX schedule.
    """
    return _build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=True, lax=True
    )


def _build_clm_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms
) -> tuple[_EventSeed, ...]:
    """
    Build the normalized CLM (Call Money) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.

    Returns:
        Tuple of event seeds for the CLM schedule.
    """
    seeds: list[_EventSeed] = []
    outstanding = terms.notional_principal
    if terms.maturity_date is not None:
        for ts in _interest_schedule(contract, terms):
            seeds.append(
                _seed_from_timestamp(
                    ts,
                    event_type="IP",
                    next_outstanding_principal=outstanding,
                    flags=enums.FLAG_CASH_EVENT,
                )
            )
        seeds.append(
            _seed_from_timestamp(
                terms.maturity_date,
                event_type="MD",
                next_outstanding_principal=0,
                flags=enums.FLAG_CASH_EVENT,
            )
        )
    seeds.extend(_rate_reset_schedule(contract, outstanding, terms.maturity_date))
    return tuple(seeds)


def _build_annuity_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> tuple[_EventSeed, ...]:
    """
    Build the ANN schedule including PRF recalculation events when needed.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the annuity schedule.

    Raises:
        ActusNormalizationError: If required fields are missing.
    """
    if terms.maturity_date is None:
        raise ActusNormalizationError(
            "ANN normalization requires maturity_date or amortization_date"
        )

    pr_schedule = _principal_schedule(contract, terms, lax=False)
    if not pr_schedule:
        raise ActusNormalizationError(
            "ANN normalization requires a principal redemption schedule"
        )

    formula_redemption_times = sorted(set(pr_schedule))
    if terms.maturity_date not in formula_redemption_times:
        formula_redemption_times.append(terms.maturity_date)

    pr_anchor = contract.principal_redemption_anchor
    if pr_anchor is None:
        pr_anchor = terms.initial_exchange_date

    pr_cycle = contract.principal_redemption_cycle
    if pr_cycle is None:
        raise ActusNormalizationError(
            "ANN normalization requires principal_redemption_cycle"
        )

    annuity_start = _annuity_start_timestamp(
        initial_exchange_date=terms.initial_exchange_date,
        principal_redemption_anchor=pr_anchor,
        principal_redemption_cycle=pr_cycle,
    )
    rate_fp = _rate_to_fp(contract.nominal_interest_rate)
    dynamic_redemption = terms.dynamic_principal_redemption
    payment_total = _resolve_annuity_payment(contract, terms, asa_decimals)

    seeds: list[_EventSeed] = []
    rr_schedule = _rate_reset_occurrences(contract, terms.maturity_date)
    if dynamic_redemption:
        if pr_anchor > terms.initial_exchange_date and formula_redemption_times:
            prf_time = pr_anchor - cst.DAY_2_SEC
            seeds.append(
                _EventSeed(
                    event_type="PRF",
                    scheduled_time=prf_time,
                    redemption_accrual_start=annuity_start,
                    redemption_accrual_end=formula_redemption_times[0],
                    flags=enums.FLAG_NON_CASH_EVENT | enums.FLAG_INITIAL_PRF,
                )
            )
        for ts, _event_type in rr_schedule:
            next_redemption = next(
                (value for value in formula_redemption_times if value > ts),
                None,
            )
            if next_redemption is None:
                continue
            seeds.append(
                _EventSeed(
                    event_type="PRF",
                    scheduled_time=ts,
                    redemption_accrual_start=ts,
                    redemption_accrual_end=next_redemption,
                    flags=enums.FLAG_NON_CASH_EVENT,
                )
            )

    rr_events = dict(rr_schedule)

    outstanding = terms.notional_principal
    previous_due = terms.initial_exchange_date
    previous_redemption = annuity_start
    for ts in pr_schedule:
        due_time = ts
        interest_due = _interest_minor_units(
            principal=outstanding,
            rate_fp=rate_fp,
            start_ts=previous_due,
            end_ts=due_time,
            day_count_convention=terms.day_count_convention,
            maturity_date=terms.maturity_date,
        )
        principal_payment = min(max(payment_total - interest_due, 0), outstanding)
        next_outstanding = max(outstanding - principal_payment, 0)

        seeds.append(
            _seed_from_timestamp(
                ts,
                event_type="PR",
                redemption_accrual_start=previous_redemption,
                redemption_accrual_end=due_time,
                next_principal_redemption=0 if dynamic_redemption else payment_total,
                next_outstanding_principal=next_outstanding,
                flags=enums.FLAG_CASH_EVENT,
            )
        )
        seeds.append(
            _seed_from_timestamp(
                ts,
                event_type="IP",
                next_principal_redemption=0 if dynamic_redemption else payment_total,
                next_outstanding_principal=next_outstanding,
                flags=enums.FLAG_CASH_EVENT,
            )
        )
        event_key = ts
        if event_key in rr_events:
            event_type = rr_events[event_key]
            seeds.append(
                _seed_from_timestamp(
                    ts,
                    event_type=event_type,
                    next_nominal_interest_rate=(
                        terms.rate_reset_next if event_type == "RRF" else 0
                    ),
                    next_outstanding_principal=outstanding,
                    flags=enums.FLAG_NON_CASH_EVENT,
                )
            )

        outstanding = next_outstanding
        previous_due = due_time
        previous_redemption = due_time

    for ts, event_type in rr_schedule:
        if any(ts == pr_ts for pr_ts in pr_schedule):
            continue
        if ts >= terms.maturity_date:
            continue
        seeds.append(
            _seed_from_timestamp(
                ts,
                event_type=event_type,
                next_nominal_interest_rate=(
                    terms.rate_reset_next if event_type == "RRF" else 0
                ),
                next_outstanding_principal=outstanding,
                flags=enums.FLAG_NON_CASH_EVENT,
            )
        )

    seeds.extend(_ipcb_schedule(contract, outstanding, terms.maturity_date))
    md_redemption_start = 0
    md_redemption_end = 0
    if not any(ts == terms.maturity_date for ts in pr_schedule):
        md_redemption_start = previous_redemption
        md_redemption_end = terms.maturity_date
    seeds.append(
        _seed_from_timestamp(
            terms.maturity_date,
            event_type="MD",
            redemption_accrual_start=md_redemption_start,
            redemption_accrual_end=md_redemption_end,
            next_principal_redemption=0 if dynamic_redemption else payment_total,
            next_outstanding_principal=0,
            flags=enums.FLAG_CASH_EVENT,
        )
    )
    return tuple(seeds)


def _build_amortizing_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
    *,
    allow_negative: bool,
    lax: bool,
) -> tuple[_EventSeed, ...]:
    """
    Build a generic amortizing schedule for LAM, NAM, and LAX.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.
        allow_negative: Whether negative amortization is allowed (NAM).
        lax: Whether this is a LAX contract with array-based schedules.

    Returns:
        Tuple of event seeds for the amortizing schedule.

    Raises:
        ActusNormalizationError: If required fields are missing.
    """
    contract_type = contract.contract_type
    if terms.maturity_date is None:
        raise ActusNormalizationError(
            f"{contract_type} normalization requires maturity_date or amortization_date"
        )

    seeds: list[_EventSeed] = []
    outstanding = terms.notional_principal
    rate_fp = _rate_to_fp(contract.nominal_interest_rate)
    pr_schedule = _principal_schedule(contract, terms, lax=lax)
    if not pr_schedule:
        raise ActusNormalizationError(
            f"{contract_type} normalization requires a principal redemption schedule"
        )

    payment_total = _to_asa_units(
        contract.next_principal_redemption_amount or 0,
        asa_decimals,
    )
    previous_due = terms.initial_exchange_date
    for index, ts in enumerate(pr_schedule):
        due_time = ts
        interest_due = _interest_minor_units(
            principal=outstanding,
            rate_fp=rate_fp,
            start_ts=previous_due,
            end_ts=due_time,
            day_count_convention=terms.day_count_convention,
            maturity_date=terms.maturity_date,
        )
        principal_payment = _principal_payment_for_period(
            contract,
            outstanding=outstanding,
            payment_total=payment_total,
            interest_due=interest_due,
            allow_negative=allow_negative,
            annuity=False,
            lax=lax,
            period_index=index,
            asa_decimals=asa_decimals,
        )
        lax_direction = _lax_direction(contract, index) if lax else "DEC"
        next_outstanding = max(outstanding - principal_payment, 0)
        if lax_direction == "INC":
            next_outstanding = outstanding + payment_total

        if principal_payment > 0:
            seeds.append(
                _seed_from_timestamp(
                    ts,
                    event_type="PR",
                    next_principal_redemption=payment_total,
                    next_outstanding_principal=next_outstanding,
                    flags=enums.FLAG_CASH_EVENT,
                )
            )
        elif lax:
            seeds.append(
                _seed_from_timestamp(
                    ts,
                    event_type="PI",
                    next_principal_redemption=payment_total,
                    next_outstanding_principal=next_outstanding,
                    flags=enums.FLAG_NON_CASH_EVENT,
                )
            )

        if interest_due > 0 or due_time == terms.maturity_date:
            seeds.append(
                _seed_from_timestamp(
                    ts,
                    event_type="IP",
                    next_principal_redemption=payment_total,
                    next_outstanding_principal=next_outstanding,
                    flags=enums.FLAG_CASH_EVENT,
                )
            )

        outstanding = next_outstanding
        previous_due = due_time

    seeds.extend(_rate_reset_schedule(contract, outstanding, terms.maturity_date))
    seeds.extend(_ipcb_schedule(contract, outstanding, terms.maturity_date))
    if outstanding:
        seeds.append(
            _seed_from_timestamp(
                terms.maturity_date,
                event_type="MD",
                next_principal_redemption=payment_total,
                next_outstanding_principal=0,
                flags=enums.FLAG_CASH_EVENT,
            )
        )
    return tuple(seeds)


def _principal_payment_for_period(
    contract: ContractAttributes,
    *,
    outstanding: int,
    payment_total: int,
    interest_due: int,
    allow_negative: bool,
    annuity: bool,
    lax: bool,
    period_index: int,
    asa_decimals: int,
) -> int:
    """
    Resolve the principal cashflow for one amortizing period.

    Calculates the principal payment amount based on contract type,
    payment structure, and period-specific parameters.

    Args:
        contract: ACTUS contract attributes.
        outstanding: Current outstanding principal.
        payment_total: Total payment amount for the period.
        interest_due: Interest amount due for the period.
        allow_negative: Whether negative amortization is allowed.
        annuity: Whether this is an annuity contract.
        lax: Whether this is a LAX contract with array-based amounts.
        period_index: Index of the current period.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Principal payment amount in ASA base units.
    """
    if lax and contract.array_pr_next is not None:
        pr_values = tuple(
            _to_asa_units(value, asa_decimals) for value in contract.array_pr_next
        )
        if period_index < len(pr_values):
            payment_total = pr_values[period_index]

    if annuity:
        return min(max(payment_total - interest_due, 0), outstanding)

    if allow_negative:
        candidate = payment_total - interest_due
        return min(max(candidate, 0), outstanding)

    return min(max(payment_total, 0), outstanding)


def _principal_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    *,
    lax: bool,
) -> tuple[int, ...]:
    """
    Resolve the principal redemption occurrence schedule.

    Generates timestamps for principal redemption events based on either
    array-based schedules (LAX) or cycle-based schedules (standard contracts).

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        lax: Whether to use LAX array-based schedule logic.

    Returns:
        Tuple of Unix timestamps for principal redemption events.

    Raises:
        ActusNormalizationError: If LAX arrays have misaligned lengths.
    """

    if lax and contract.array_pr_anchor is not None:
        anchors = tuple(ts for ts in contract.array_pr_anchor)
        cycles = tuple(contract.array_pr_cycle or ())
        increases = tuple(value for value in contract.array_increase_decrease or ())
        if increases and len(increases) != len(contract.array_pr_anchor):
            raise ActusNormalizationError(
                "LAX array_pr_* schedules must have aligned lengths"
            )
        if cycles:
            timestamps = resolve_array_schedule(
                anchors,
                cycles,
                terms.maturity_date,
                end_of_month_convention=contract.end_of_month_convention,
                business_day_convention=contract.business_day_convention,
                calendar=contract.calendar,
            )
        else:
            timestamps = tuple(anchor for anchor in anchors)
        return tuple(
            ts
            for ts in _deduplicate_timestamps(timestamps)
            if terms.initial_exchange_date < ts <= terms.maturity_date
        )

    anchor = contract.principal_redemption_anchor
    cycle = contract.principal_redemption_cycle
    if anchor is None or cycle is None or terms.maturity_date is None:
        return ()
    timestamps = resolve_cycle_schedule(
        anchor,
        cycle,
        terms.maturity_date,
        end_of_month_convention=contract.end_of_month_convention,
        business_day_convention=contract.business_day_convention,
        calendar=contract.calendar,
    )
    if cycle.stub == "+" and timestamps:
        if timestamps[-1] != terms.maturity_date:
            timestamps = timestamps[:-1]
    return tuple(
        ts
        for ts in timestamps
        if terms.initial_exchange_date <= ts < terms.maturity_date
    )


def _interest_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
) -> tuple[UTCTimeStamp, ...]:
    """
    Resolve the interest payment occurrence schedule.

    Generates timestamps for interest payment (IP) events based on the
    interest payment cycle. Ensures maturity date is included and all
    events fall within the contract's active period (after IED, up to MD).

    The function handles cycle suffixes:
    - If cycle ends with "+", the last event is adjusted to maturity_date
    - Otherwise, maturity_date is appended to the schedule

    Args:
        contract: ACTUS contract attributes with interest payment parameters.
        terms: Normalized contract terms with IED and maturity date.

    Returns:
        Tuple of Unix timestamps for interest payment events, deduplicated
        and filtered to (IED, maturity_date]. Returns empty tuple if
        interest_payment_anchor, interest_payment_cycle, or maturity_date
        are not specified.

    Example:
        >>> # Monthly interest payments from Feb to Dec 2021
        >>> contract = ContractAttributes(
        ...     interest_payment_anchor=1612137600,  # 2021-02-01
        ...     interest_payment_cycle=Cycle(count=1, unit="M"),
        ...     ...
        ... )
        >>> terms = NormalizedActusTerms(
        ...     initial_exchange_date=1609459200,  # 2021-01-01
        ...     maturity_date=1640995200,  # 2022-01-01
        ...     ...
        ... )
        >>> schedule = _interest_schedule(contract, terms)
        # Returns timestamps: [Feb 1, Mar 1, ..., Dec 1, Jan 1 2022]
    """

    anchor = contract.interest_payment_anchor
    cycle = contract.interest_payment_cycle
    if anchor is None or cycle is None or terms.maturity_date is None:
        return ()

    timestamps = list(
        resolve_cycle_schedule(
            anchor,
            cycle,
            terms.maturity_date,
            end_of_month_convention=contract.end_of_month_convention,
            business_day_convention=contract.business_day_convention,
            calendar=contract.calendar,
        )
    )
    timestamps = [
        ts
        for ts in timestamps
        if terms.initial_exchange_date < ts <= terms.maturity_date
    ]
    if timestamps:
        md_present = terms.maturity_date in timestamps
        if not md_present:
            maturity_date = terms.maturity_date
            if cycle.stub == "+":
                timestamps[-1] = maturity_date
            else:
                timestamps.append(maturity_date)
    return tuple(_deduplicate_timestamps(timestamps))


def _rate_reset_schedule(
    contract: ContractAttributes,
    outstanding: int,
    maturity_date: int | None,
) -> tuple[_EventSeed, ...]:
    """
    Build non-cash RR/RRF event seeds from the rate reset schedule.

    Creates RR (Rate Reset) and RRF (Rate Reset with Fixed spread) event seeds
    that update the interest rate without cash flows.

    Args:
        contract: ACTUS contract attributes.
        outstanding: Current outstanding principal.
        maturity_date: Contract maturity date.

    Returns:
        Tuple of rate reset event seeds.
    """
    if maturity_date is None:
        return ()
    next_rate = _rate_to_fp(
        contract.rate_reset_next
        if contract.rate_reset_next is not None
        else contract.nominal_interest_rate
    )
    return tuple(
        _seed_from_timestamp(
            ts,
            event_type=event_type,
            next_nominal_interest_rate=next_rate if event_type == "RRF" else 0,
            next_outstanding_principal=outstanding,
            flags=enums.FLAG_NON_CASH_EVENT,
        )
        for ts, event_type in _rate_reset_occurrences(contract, maturity_date)
    )


def _rate_reset_occurrences(
    contract: ContractAttributes,
    maturity_date: int | None,
) -> tuple[tuple[int, str], ...]:
    """
    Resolve rate reset occurrences and label them as RR or RRF.

    Generates tuples of (timestamp, event_type) for rate reset events,
    distinguishing between simple resets (RR) and fixed resets (RRF).

    Args:
        contract: ACTUS contract attributes.
        maturity_date: Contract maturity date.

    Returns:
        Tuple of (timestamp, event_type) pairs for rate reset events.
    """
    anchor = contract.rate_reset_anchor
    cycle = contract.rate_reset_cycle
    if anchor is None or cycle is None or maturity_date is None:
        return ()

    timestamps = tuple(
        ts
        for ts in resolve_cycle_schedule(
            anchor,
            cycle,
            maturity_date,
            end_of_month_convention=contract.end_of_month_convention,
            business_day_convention=contract.business_day_convention,
            calendar=contract.calendar,
        )
        if ts < maturity_date
    )
    if not timestamps:
        return ()

    first_is_rrf = contract.rate_reset_next is not None
    return tuple(
        (ts, "RRF" if first_is_rrf and index == 0 else "RR")
        for index, ts in enumerate(timestamps)
    )


def _ipcb_schedule(
    contract: ContractAttributes,
    outstanding: int,
    maturity_date: int | None,
) -> tuple[_EventSeed, ...]:
    """
    Build IPCB event seeds for interest calculation base adjustments.

    IPCB (Interest Payment Calculation Base) events adjust the base amount
    used for interest calculations without generating cash flows.

    Args:
        contract: ACTUS contract attributes.
        outstanding: Current outstanding principal.
        maturity_date: Contract maturity date.

    Returns:
        Tuple of IPCB event seeds.
    """
    anchor = contract.interest_calculation_base_anchor
    cycle = contract.interest_calculation_base_cycle
    if anchor is None or cycle is None or maturity_date is None:
        return ()
    return tuple(
        _seed_from_timestamp(
            ts,
            event_type="IPCB",
            next_outstanding_principal=outstanding,
            flags=enums.FLAG_NON_CASH_EVENT,
        )
        for ts in resolve_cycle_schedule(
            anchor,
            cycle,
            maturity_date,
            end_of_month_convention=contract.end_of_month_convention,
            business_day_convention=contract.business_day_convention,
            calendar=contract.calendar,
        )
        if ts <= maturity_date
    )


def _seed_from_preprocessed(
    event_id: int, item: ObservedEventRequest | ExecutionScheduleEntry
) -> _EventSeed:
    """
    Convert a preprocessed event payload into an intermediate event seed.

    Handles both ObservedEventRequest and ExecutionScheduleEntry types,
    converting them to the internal _EventSeed representation.

    Args:
        event_id: Unique identifier for the event.
        item: Preprocessed event or schedule entry.

    Returns:
        Event seed representation of the preprocessed event.
    """
    if isinstance(item, ExecutionScheduleEntry):
        return _EventSeed(
            event_type=item.event_type,
            scheduled_time=item.scheduled_time,
            accrual_factor=item.accrual_factor,
            redemption_accrual_factor=item.redemption_accrual_factor,
            next_nominal_interest_rate=item.next_nominal_interest_rate,
            next_principal_redemption=item.next_principal_redemption,
            next_outstanding_principal=item.next_outstanding_principal,
            flags=item.flags,
        )
    entry = item.to_schedule_entry(event_id)
    return _seed_from_preprocessed(event_id, entry)


def _seed_sort_key(seed: _EventSeed) -> tuple[int, int, str]:
    """
    Return the deterministic ACTUS event ordering key for a seed.

    Events are ordered by: (1) scheduled time, (2) priority, (3) event type.
    Ensures deterministic ordering when multiple events occur at the same time.

    Args:
        seed: Event seed to generate sort key for.

    Returns:
        Tuple of (scheduled_time, priority, event_type) for sorting.
    """
    priority = EVENT_SCHEDULE_PRIORITY.get(seed.event_type, 99)
    return seed.scheduled_time, priority, seed.event_type


def _initial_next_principal_redemption(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> int:
    """
    Resolve the initial next principal redemption for the first IED state.

    For ANN contracts, calculates the annuity payment amount.
    For other contracts, uses the configured next_principal_redemption_amount.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Initial principal redemption amount in ASA base units.
    """
    if contract.contract_type != "ANN":
        if contract.next_principal_redemption_amount is None:
            return 0
        return _to_asa_units(contract.next_principal_redemption_amount, asa_decimals)
    return _resolve_annuity_payment(contract, terms, asa_decimals)


def _resolve_annuity_payment(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> int:
    """
    Resolve the initial annuity payment amount from terms or formula.

    For ANN contracts, either uses the configured payment amount or calculates
    it using the annuity formula based on present value of cash flows.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Annuity payment amount in ASA base units.

    Raises:
        ActusNormalizationError: If required fields are missing.
    """

    payment_total = _to_asa_units(
        contract.next_principal_redemption_amount, asa_decimals
    )
    if not terms.dynamic_principal_redemption and payment_total > 0:
        return payment_total

    # Use maturity_date or amortization_date (whichever is set)
    end_date = contract.maturity_date or contract.amortization_date
    if end_date is None:
        raise ActusNormalizationError(
            "ANN normalization requires maturity_date or amortization_date"
        )

    pr_schedule = _principal_schedule(contract, terms, lax=False)
    if not pr_schedule:
        raise ActusNormalizationError(
            "ANN normalization requires a principal redemption schedule"
        )

    formula_redemption_dates = sorted(set(pr_schedule))
    if terms.maturity_date not in formula_redemption_dates:
        formula_redemption_dates.append(terms.maturity_date)

    pr_anchor = contract.principal_redemption_anchor
    if pr_anchor is None:
        pr_anchor = terms.initial_exchange_date
    pr_cycle = contract.principal_redemption_cycle
    if pr_cycle is None:
        raise ActusNormalizationError(
            "ANN normalization requires principal_redemption_cycle"
        )

    annuity_start = _annuity_start_timestamp(
        initial_exchange_date=terms.initial_exchange_date,
        principal_redemption_anchor=pr_anchor,
        principal_redemption_cycle=pr_cycle,
    )
    return _calculate_annuity_payment(
        start_ts=annuity_start,
        redemption_schedule=formula_redemption_dates,
        notional=terms.notional_principal,
        accrued_interest=0,
        rate_fp=_rate_to_fp(contract.nominal_interest_rate),
        day_count_convention=terms.day_count_convention,
        maturity_date=terms.maturity_date,
    )


def _lax_direction(contract: ContractAttributes, period_index: int) -> str:
    """
    Return whether a LAX period decreases or increases principal.

    Uses array_increase_decrease to determine if a period generates
    a principal increase (INC) or decrease (DEC) event.

    Args:
        contract: ACTUS contract attributes.
        period_index: Zero-based index of the period.

    Returns:
        "INC" for increase or "DEC" for decrease (default).
    """
    directions = tuple(
        str(value).upper() for value in contract.array_increase_decrease or ()
    )
    if period_index < len(directions):
        return directions[period_index]
    return "DEC"


def _interest_minor_units(
    *,
    principal: int,
    rate_fp: int,
    start_ts: int,
    end_ts: int,
    day_count_convention: int,
    maturity_date: int | None,
) -> int:
    """
    Compute interest in minor units for a principal and accrual interval.

    Calculates interest as: principal * rate * year_fraction, where rate
    and year_fraction are in fixed-point representation.

    Example:
        >>> _interest_minor_units(
        ...     principal=100000,
        ...     rate_fp=50000000,  # 5% in fixed-point
        ...     start_ts=1609459200,
        ...     end_ts=1612137600,
        ...     day_count_convention=2,  # 30/360
        ...     maturity_date=None
        ... )

    Args:
        principal: Principal amount in ASA base units.
        rate_fp: Interest rate in fixed-point representation.
        start_ts: Accrual start timestamp.
        end_ts: Accrual end timestamp.
        day_count_convention: Day count convention code.
        maturity_date: Optional maturity date for year fraction calculation.

    Returns:
        Interest amount in ASA base units.
    """
    if rate_fp <= 0 or end_ts <= start_ts:
        return 0
    year_fraction = year_fraction_fixed(
        start_ts,
        end_ts,
        day_count_convention=day_count_convention,
        maturity_date=maturity_date,
    )
    return (
        principal
        * rate_fp
        * year_fraction
        // cst.FIXED_POINT_SCALE
        // cst.FIXED_POINT_SCALE
    )


def _subtract_one_cycle(timestamp: UTCTimeStamp, cycle: Cycle) -> int:
    """
    Move one ACTUS cycle backward from a timestamp.

    Supports daily (D), weekly (W), monthly (M), quarterly (Q),
    semi-annual (H), and yearly (Y) cycles.

    Example:
        >>> cycle = Cycle(count=1, unit="M")
        >>> _subtract_one_cycle(1612137600, cycle)  # 2021-02-01 -> 2021-01-01

    Args:
        timestamp: Starting Unix timestamp.
        cycle: ACTUS cycle specification.

    Returns:
        Unix timestamp one cycle earlier.

    Raises:
        ActusNormalizationError: If cycle unit is unsupported.
    """

    if cycle.unit == "D":
        return timestamp - cycle.count * cst.DAY_2_SEC

    if cycle.unit == "W":
        return timestamp - cycle.count * 7 * cst.DAY_2_SEC

    month_delta_map = {"M": 1, "Q": 3, "H": 6, "Y": 12}
    if cycle.unit not in month_delta_map:
        raise ActusNormalizationError(f"Unsupported ACTUS cycle unit: {cycle.unit}")

    current = timestamp_to_datetime(timestamp)
    months = cycle.count * month_delta_map[cycle.unit]
    month_index = (current.month - 1) - months
    year = current.year + month_index // 12
    month = (month_index % 12) + 1
    day = min(current.day, days_in_month(year, month))
    return datetime_to_timestamp(current.replace(year=year, month=month, day=day))


def _annuity_start_timestamp(
    *,
    initial_exchange_date: UTCTimeStamp,
    principal_redemption_anchor: UTCTimeStamp,
    principal_redemption_cycle: Cycle,
) -> int:
    """
    Return the start timestamp used by the ANN payment formula.

    The annuity calculation starts from the later of: IED or one cycle
    before the first principal redemption.

    Args:
        initial_exchange_date: Contract IED timestamp.
        principal_redemption_anchor: Anchor date for principal redemptions.
        principal_redemption_cycle: Principal redemption cycle.

    Returns:
        Start timestamp for annuity calculation.
    """
    return max(
        initial_exchange_date,
        _subtract_one_cycle(principal_redemption_anchor, principal_redemption_cycle),
    )


def _calculate_annuity_payment(
    *,
    start_ts: int,
    redemption_schedule: Sequence[int],
    notional: int,
    accrued_interest: int,
    rate_fp: int,
    day_count_convention: int,
    maturity_date: int | None,
) -> int:
    """
    Calculate an annuity payment from a redemption schedule and rate path.

    Uses the present value formula to compute the constant payment amount
    that amortizes the principal plus accrued interest over the schedule.

    Args:
        start_ts: Calculation start timestamp.
        redemption_schedule: Sequence of payment timestamps.
        notional: Principal amount in ASA base units.
        accrued_interest: Accrued interest at start.
        rate_fp: Interest rate in fixed-point representation.
        day_count_convention: Day count convention code.
        maturity_date: Optional maturity date for calculations.

    Returns:
        Annuity payment amount in ASA base units.
    """
    remaining = tuple(due_ts for due_ts in redemption_schedule if due_ts > start_ts)
    if not remaining:
        return 0

    discount_fp = cst.FIXED_POINT_SCALE
    denominator_fp = 0
    previous_ts = start_ts
    for due_ts in remaining:
        period_factor = year_fraction_fixed(
            previous_ts,
            due_ts,
            day_count_convention=day_count_convention,
            maturity_date=maturity_date,
        )
        period_rate = cst.FIXED_POINT_SCALE + (
            rate_fp * period_factor // cst.FIXED_POINT_SCALE
        )
        if period_rate <= 0:
            raise ActusNormalizationError(
                "Invalid ANN redemption schedule discount factor"
            )
        discount_fp = discount_fp * cst.FIXED_POINT_SCALE // period_rate
        denominator_fp += discount_fp
        previous_ts = due_ts

    if denominator_fp <= 0:
        raise ActusNormalizationError(
            "ANN normalization requires a positive annuity denominator"
        )
    numerator = max(notional, 0) + max(accrued_interest, 0)
    return numerator * cst.FIXED_POINT_SCALE // denominator_fp


def _seed_from_timestamp(
    timestamp: UTCTimeStamp,
    *,
    event_type: str,
    redemption_accrual_start: UTCTimeStamp = 0,
    redemption_accrual_end: UTCTimeStamp = 0,
    next_nominal_interest_rate: int = 0,
    next_principal_redemption: int = 0,
    next_outstanding_principal: int = 0,
    flags: int = 0,
) -> _EventSeed:
    """
    Create an intermediate event seed from a resolved schedule timestamp.

    Factory function for creating _EventSeed instances with default values
    for optional fields.

    Args:
        timestamp: Unix timestamp when event occurs.
        event_type: ACTUS event type (e.g., "IED", "IP", "PR").
        redemption_accrual_start: Start of redemption accrual period.
        redemption_accrual_end: End of redemption accrual period.
        next_nominal_interest_rate: Interest rate after this event.
        next_principal_redemption: Principal redemption amount.
        next_outstanding_principal: Outstanding principal after event.
        flags: Event flags (cash/non-cash, etc.).

    Returns:
        Event seed with specified parameters.
    """
    return _EventSeed(
        event_type=event_type,
        scheduled_time=timestamp,
        redemption_accrual_start=redemption_accrual_start,
        redemption_accrual_end=redemption_accrual_end,
        next_nominal_interest_rate=next_nominal_interest_rate,
        next_principal_redemption=next_principal_redemption,
        next_outstanding_principal=next_outstanding_principal,
        flags=flags,
    )
