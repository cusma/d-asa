"""Annuity payment calculation for ANN contracts."""

from __future__ import annotations

from collections.abc import Sequence

from smart_contracts import constants as cst

from ..contracts import ContractAttributes
from ..day_count import days_in_month, year_fraction_fixed
from ..errors import ActusNormalizationError
from ..models import NormalizedActusTerms
from ..schedule import Cycle, datetime_to_timestamp, timestamp_to_datetime
from ..unix_time import UTCTimeStamp
from .conversions import rate_to_fp, to_asa_units
from .schedules import resolve_principal_schedule


def subtract_one_cycle(timestamp: UTCTimeStamp, cycle: Cycle) -> int:
    """
    Move one ACTUS cycle backward from a timestamp.

    Supports daily (D), weekly (W), monthly (M), quarterly (Q),
    semi-annual (H), and yearly (Y) cycles.

    Example:
        >>> cycle = Cycle(count=1, unit="M")
        >>> subtract_one_cycle(1612137600, cycle)  # 2021-02-01 -> 2021-01-01

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


def get_annuity_start_timestamp(
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
        subtract_one_cycle(principal_redemption_anchor, principal_redemption_cycle),
    )


def calculate_annuity_payment(
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


def resolve_annuity_payment(
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
    payment_total = to_asa_units(
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

    pr_schedule = resolve_principal_schedule(
        contract, terms, lax=False, end_date=end_date
    )
    if not pr_schedule:
        raise ActusNormalizationError(
            "ANN normalization requires a principal redemption schedule"
        )

    formula_redemption_dates = sorted(set(pr_schedule))
    if end_date not in formula_redemption_dates:
        formula_redemption_dates.append(end_date)

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
    return calculate_annuity_payment(
        start_ts=annuity_start,
        redemption_schedule=formula_redemption_dates,
        notional=terms.notional_principal,
        accrued_interest=0,
        rate_fp=rate_to_fp(contract.nominal_interest_rate),
        day_count_convention=terms.day_count_convention,
        maturity_date=end_date,
    )
