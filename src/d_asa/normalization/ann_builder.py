"""ANN (Annuity) schedule builder for ACTUS normalization."""

from __future__ import annotations

from .. import constants as cst
from .. import enums
from ..contracts import ContractAttributes
from ..errors import ActusNormalizationError
from ..models import NormalizedActusTerms
from .annuity import get_annuity_start_timestamp, resolve_annuity_payment
from .calculations import calculate_interest, interpolate_balance_at_timestamp
from .conversions import rate_to_fp
from .event_seeds import EventSeed, create_seed
from .schedules import resolve_principal_schedule, resolve_rate_reset_occurrences


def build_ipcb_seeds(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    balance_timeline: list[tuple[int, int]],
    initial_principal: int,
) -> tuple[EventSeed, ...]:
    """Helper to import from builders to avoid circular dependency."""
    from .builders import build_ipcb_seeds as _build_ipcb_seeds

    return _build_ipcb_seeds(contract, terms, balance_timeline, initial_principal)


def build_ann_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> tuple[EventSeed, ...]:
    """
    Build the normalized ANN (Annuity) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the ANN schedule.
    """
    # Use maturity_date or amortization_date (whichever is set)
    end_date = terms.maturity_date or contract.amortization_date
    if end_date is None:
        raise ActusNormalizationError(
            "ANN normalization requires maturity_date or amortization_date"
        )

    pr_schedule = resolve_principal_schedule(
        contract, terms, lax=False, end_date=end_date
    )
    if not pr_schedule:
        raise ActusNormalizationError(
            "ANN normalization requires a principal redemption schedule"
        )

    formula_redemption_times = sorted(set(pr_schedule))
    if end_date not in formula_redemption_times:
        formula_redemption_times.append(end_date)

    pr_anchor = contract.principal_redemption_anchor
    if pr_anchor is None:
        pr_anchor = terms.initial_exchange_date

    pr_cycle = contract.principal_redemption_cycle
    if pr_cycle is None:
        raise ActusNormalizationError(
            "ANN normalization requires principal_redemption_cycle"
        )

    annuity_start = get_annuity_start_timestamp(
        initial_exchange_date=terms.initial_exchange_date,
        principal_redemption_anchor=pr_anchor,
        principal_redemption_cycle=pr_cycle,
    )
    rate_fp = rate_to_fp(contract.nominal_interest_rate)
    dynamic_redemption = terms.dynamic_principal_redemption
    payment_total = resolve_annuity_payment(contract, terms, asa_decimals)

    seeds: list[EventSeed] = []
    rr_schedule = resolve_rate_reset_occurrences(contract, terms)
    next_rate = rate_to_fp(
        contract.rate_reset_next
        if contract.rate_reset_next is not None
        else contract.nominal_interest_rate
    )

    if dynamic_redemption:
        if pr_anchor > terms.initial_exchange_date and formula_redemption_times:
            prf_time = pr_anchor - cst.DAY_2_SEC
            seeds.append(
                EventSeed(
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
                EventSeed(
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
    # Track balance timeline for interpolation
    balance_timeline: list[tuple[int, int]] = []

    for ts in pr_schedule:
        due_time = ts
        interest_due = calculate_interest(
            principal=outstanding,
            rate_fp=rate_fp,
            start_ts=previous_due,
            end_ts=due_time,
            day_count_convention=terms.day_count_convention,
            maturity_date=end_date,
        )
        principal_payment = min(max(payment_total - interest_due, 0), outstanding)
        next_outstanding = max(outstanding - principal_payment, 0)

        # Record balance change
        balance_timeline.append((ts, next_outstanding))

        seeds.append(
            create_seed(
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
            create_seed(
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
                create_seed(
                    ts,
                    event_type=event_type,
                    next_nominal_interest_rate=(
                        next_rate if event_type == "RRF" else 0
                    ),
                    next_outstanding_principal=next_outstanding,
                    flags=enums.FLAG_NON_CASH_EVENT,
                )
            )

        outstanding = next_outstanding
        previous_due = due_time
        previous_redemption = due_time

    # Add non-coincident reset events with interpolated balance
    for ts, event_type in rr_schedule:
        if any(ts == pr_ts for pr_ts in pr_schedule):
            continue
        if ts >= end_date:
            continue
        # Interpolate balance at this timestamp
        balance_at_reset = interpolate_balance_at_timestamp(
            ts, balance_timeline, terms.notional_principal
        )
        seeds.append(
            create_seed(
                ts,
                event_type=event_type,
                next_nominal_interest_rate=(next_rate if event_type == "RRF" else 0),
                next_outstanding_principal=balance_at_reset,
                flags=enums.FLAG_NON_CASH_EVENT,
            )
        )

    seeds.extend(
        build_ipcb_seeds(contract, terms, balance_timeline, terms.notional_principal)
    )
    md_redemption_start = 0
    md_redemption_end = 0
    if not any(ts == end_date for ts in pr_schedule):
        md_redemption_start = previous_redemption
        md_redemption_end = end_date
    seeds.append(
        create_seed(
            end_date,
            event_type="MD",
            redemption_accrual_start=md_redemption_start,
            redemption_accrual_end=md_redemption_end,
            next_principal_redemption=0 if dynamic_redemption else payment_total,
            next_outstanding_principal=0,
            flags=enums.FLAG_CASH_EVENT,
        )
    )
    return tuple(seeds)
