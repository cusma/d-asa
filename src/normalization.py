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
    Normalize an amount into ASA's units (uint64).

    Example:
        1) amount=100.42, asa_decimals=3, the result in ASA's units is 100420
        2) amount=100, asa_decimals=2, the result in ASA's units is 10000

    Args:
        amount: The numeric value to normalize.
        asa_decimals: The number of decimal places for the ASA.

    Raises:
        TypeError: if the value is not an int, float, or Decimal.
        ActusNormalizationError: if the result exceeds uint64 max.
    """

    if isinstance(amount, (int, float, Decimal)):
        scale = 10**asa_decimals
        result = int(Decimal(str(asa_decimals)) * scale)
    else:
        raise TypeError(f"Unsupported value type: {type(amount)}")

    if result < 0 or result > cst.MAX_UINT64:
        raise ActusNormalizationError(
            f"Value {amount} results in {result} which exceeds uint64 bounds"
        )

    return result


def _rate_to_fp(value: int | float | Decimal) -> int:
    """
    Normalize numeric decimal rates into AVM-compatible uint64 integer fixed-point
    scaled units.

    Always scales by FIXED_POINT_SCALE to convert decimal-like values to fixed point
    precision integers.

    Example:
        A rate of 0.05 (5%) with FIXED_POINT_SCALE of 1_000_000_000 becomes 50_000_000.

    Args:
        value: The rate value to normalize.

    Raises:
        TypeError: if the value is not an int, float, or Decimal.
        ActusNormalizationError: if the result exceeds uint64 max.
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
    notional = _to_asa_units(notional, asa_decimals)
    pdied = _to_asa_units(premium_discount_at_ied, asa_decimals)
    return notional - pdied


def _deduplicate_timestamps(ts: Sequence[UTCTimeStamp]) -> tuple[UTCTimeStamp, ...]:
    """Remove duplicate timestamps while preserving sorted schedule order."""
    return tuple(dict.fromkeys(sorted(ts)))


@dataclass(frozen=True, slots=True)
class _EventSeed:
    """Intermediate normalized event before final schedule encoding."""

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
    fixed_point_scale: int = cst.FIXED_POINT_SCALE,
    preprocessed_events: (
        Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None
    ) = None,
) -> NormalizationResult:
    """Normalize raw ACTUS attributes into terms, schedule, and initial state.

    Args:
        contract: ACTUS contract attributes.
        denomination_asset_id: The denomination ASA ID.
        denomination_asset_decimals: The decimal places od the denomination ASA.
        notional_unit_value: The notional unit value to be converted in denomination ASA.
        secondary_market_opening_date: Optional secondary market opening date.
        secondary_market_closure_date: Optional secondary market closure date.
        fixed_point_scale: The fixed point scaling.
        preprocessed_events: Optional preprocessed events.
    """

    if contract.status_date >= contract.initial_exchange_date:
        raise ActusNormalizationError(
            "D-ASA requires status_date to be strictly before initial_exchange_date"
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
        contract_type=CONTRACT_TYPE_IDS[contract.contract_type],
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
        next_principal_redemption_amount=contract.next_principal_redemption_amount,
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
        fixed_point_scale=fixed_point_scale,
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
    """Turn intermediate event seeds into AVM schedule entries."""
    if preprocessed_events is not None:
        seeds = [
            _seed_from_preprocessed(index, item)
            for index, item in enumerate(preprocessed_events)
        ]
    else:
        seeds = list(
            _build_schedule_seeds(
                contract, terms, contract_type=contract_type, asa_decimals=asa_decimals
            )
        )

    if not any(seed.event_type == "IED" for seed in seeds):
        seeds.append(_initial_exchange_seed(contract, terms, asa_decimals=asa_decimals))

    ordered = sorted(seeds, key=_seed_sort_key)
    allowed = ALLOWED_EVENT_TYPES[contract_type]
    entries: list[ExecutionScheduleEntry] = []
    previous_ts = status_date
    for event_id, seed in enumerate(ordered):
        if seed.event_type not in allowed:
            raise UnsupportedActusFeatureError(
                f"Unsupported event {seed.event_type} for {contract_type}"
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
    """Dispatch contract-type-specific schedule construction."""
    dispatch = {
        "PAM": _build_pam_schedule,
        "LAM": _build_lam_schedule,
        "NAM": _build_nam_schedule,
        "ANN": _build_ann_schedule,
        "LAX": _build_lax_schedule,
        "CLM": _build_clm_schedule,
    }
    return dispatch[contract_type](contract, terms, asa_decimals=asa_decimals)


def _initial_exchange_seed(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> _EventSeed:
    """Build the mandatory initial exchange event seed."""

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
    """Build the normalized PAM event seed schedule."""

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
    """Build the normalized LAM event seed schedule."""
    return _build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=False, lax=False
    )


def _build_nam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """Build the normalized NAM event seed schedule."""
    return _build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=True, lax=False
    )


def _build_ann_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """Build the normalized ANN event seed schedule."""
    return _build_annuity_schedule(contract, terms, asa_decimals)


def _build_lax_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[_EventSeed, ...]:
    """Build the normalized LAX event seed schedule."""
    return _build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=True, lax=True
    )


def _build_clm_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms
) -> tuple[_EventSeed, ...]:
    """Build the normalized CLM event seed schedule."""
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
    """Build the ANN schedule including PRF recalculation events when needed."""
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
    """Build a generic amortizing schedule for LAM, NAM, and LAX."""
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
    """Resolve the principal cashflow for one amortizing period."""
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
    """Resolve the principal redemption occurrence schedule."""

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
    """Resolve the interest payment occurrence schedule."""

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
            if str(cycle).upper().endswith("+"):
                timestamps[-1] = maturity_date
            else:
                timestamps.append(maturity_date)
    return tuple(_deduplicate_timestamps(timestamps))


def _rate_reset_schedule(
    contract: ContractAttributes,
    outstanding: int,
    maturity_date: int | None,
) -> tuple[_EventSeed, ...]:
    """Build non-cash RR/RRF seeds from the normalized reset schedule."""
    if maturity_date is None:
        return ()
    next_rate = (
        _rate_to_fp(
            contract.rate_reset_next
            if contract.rate_reset_next is not None
            else contract.nominal_interest_rate
        ),
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
    """Resolve rate reset occurrences and label them as RR or RRF."""
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
    """Build IPCB seeds for interest calculation base adjustments."""
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
    """Convert a preprocessed event payload into an intermediate event seed."""
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
    """Return the deterministic ACTUS event ordering key for a seed."""
    priority = EVENT_SCHEDULE_PRIORITY.get(seed.event_type, 99)
    return seed.scheduled_time, priority, seed.event_type


def _initial_next_principal_redemption(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> int:
    """Resolve the initial next principal redemption term for the first IED state."""
    if contract.contract_type != "ANN":
        return _to_asa_units(contract.next_principal_redemption_amount, asa_decimals)
    return _resolve_annuity_payment(contract, terms, asa_decimals)


def _resolve_annuity_payment(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> int:
    """Resolve the initial annuity payment amount from terms or formula."""

    payment_total = _to_asa_units(
        contract.next_principal_redemption_amount, asa_decimals
    )
    if not terms.dynamic_principal_redemption and payment_total > 0:
        return payment_total

    if contract.maturity_date is None or contract.amortization_date is None:
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
    """Return whether a LAX period decreases or increases principal."""
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
    """Compute interest in minor units for a principal and accrual interval."""
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
    """Move one ACTUS cycle backward from a timestamp."""

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
    """Return the start timestamp used by the ANN payment formula."""
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
    """Calculate an annuity payment from a redemption schedule and rate path."""
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
    """Create an intermediate event seed from a resolved schedule timestamp."""
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
