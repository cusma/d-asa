"""Financial calculation utilities for ACTUS normalization."""

from __future__ import annotations

from smart_contracts import constants as cst

from ..day_count import year_fraction_fixed


def calculate_interest(
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
        >>> calculate_interest(
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


def interpolate_balance_at_timestamp(
    timestamp: int,
    balance_timeline: list[tuple[int, int]],
    initial_balance: int,
) -> int:
    """
    Interpolate the outstanding principal balance at a specific timestamp.

    Args:
        timestamp: The timestamp to query.
        balance_timeline: List of (timestamp, balance_after) tuples in chronological order.
        initial_balance: The starting balance before any events.

    Returns:
        The outstanding balance at the given timestamp.
    """
    if not balance_timeline:
        return initial_balance

    # If timestamp is before first event, return initial balance
    if timestamp < balance_timeline[0][0]:
        return initial_balance

    # Find the last event on or before the timestamp
    balance = initial_balance
    for ts, balance_after in balance_timeline:
        if ts <= timestamp:
            balance = balance_after
        else:
            break

    return balance


def calculate_principal_payment(
    *,
    outstanding: int,
    payment_total: int,
    interest_due: int,
    allow_negative: bool,
    annuity: bool,
    lax: bool,
    period_index: int,
    pr_values_scaled: tuple[int, ...] | None = None,
) -> tuple[int, int]:
    """
    Resolve the principal cashflow for one amortizing period.

    Calculates the principal payment amount based on contract type,
    payment structure, and period-specific parameters.

    Args:
        outstanding: Current outstanding principal.
        payment_total: Total payment amount for the period.
        interest_due: Interest amount due for the period.
        allow_negative: Whether negative amortization is allowed.
        annuity: Whether this is an annuity contract.
        lax: Whether this is a LAX contract with array-based amounts.
        period_index: Index of the current period.
        pr_values_scaled: Precomputed scaled principal values for LAX contracts.

    Returns:
        Tuple of (principal_payment, payment_total) where payment_total may be
        updated from array_pr_next for LAX contracts.
    """
    # For LAX contracts, override payment_total with period-specific value
    if lax and pr_values_scaled is not None and period_index < len(pr_values_scaled):
        payment_total = pr_values_scaled[period_index]

    if annuity:
        return min(max(payment_total - interest_due, 0), outstanding), payment_total

    if allow_negative:
        # For NAM, allow negative principal payments (representing capitalization)
        # When payment_total < interest_due, the difference is capitalized
        candidate = payment_total - interest_due
        # Clamp negative values to prevent exceeding outstanding balance
        # and positive values to not exceed outstanding
        return max(min(candidate, outstanding), -outstanding), payment_total

    return min(max(payment_total, 0), outstanding), payment_total
