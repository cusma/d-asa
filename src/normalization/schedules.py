"""Schedule resolution utilities for ACTUS contracts."""

from __future__ import annotations

from ..contracts import ContractAttributes
from ..errors import ActusNormalizationError
from ..models import NormalizedActusTerms
from ..schedule import Cycle, resolve_array_schedule, resolve_cycle_schedule
from ..unix_time import UTCTimeStamp
from .event_seeds import deduplicate_timestamps


def resolve_principal_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    *,
    lax: bool,
    end_date: int | None = None,
) -> tuple[int, ...]:
    """
    Resolve the principal redemption occurrence schedule.

    Generates timestamps for principal redemption events based on either
    array-based schedules (LAX) or cycle-based schedules (standard contracts).

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        lax: Whether to use LAX array-based schedule logic.
        end_date: Explicit end date for the schedule. If not provided, falls back to terms.maturity_date.

    Returns:
        Tuple of Unix timestamps for principal redemption events.

    Raises:
        ActusNormalizationError: If LAX arrays have misaligned lengths.
    """
    if lax and contract.array_pr_anchor is not None:
        anchors = tuple(ts for ts in contract.array_pr_anchor)
        cycles = tuple(contract.array_pr_cycle or ())
        increases = tuple(value for value in contract.array_increase_decrease or ())
        pr_next = tuple(contract.array_pr_next or ())

        anchor_len = len(anchors)

        # Validate all LAX arrays have aligned lengths
        if cycles and len(cycles) != anchor_len:
            raise ActusNormalizationError(
                f"LAX array_pr_cycle length ({len(cycles)}) must match "
                f"array_pr_anchor length ({anchor_len})"
            )
        if increases and len(increases) != anchor_len:
            raise ActusNormalizationError(
                f"LAX array_increase_decrease length ({len(increases)}) must match "
                f"array_pr_anchor length ({anchor_len})"
            )
        if pr_next and len(pr_next) != anchor_len:
            raise ActusNormalizationError(
                f"LAX array_pr_next length ({len(pr_next)}) must match "
                f"array_pr_anchor length ({anchor_len})"
            )

        # Use provided end_date or fall back to terms.maturity_date
        effective_end = end_date if end_date is not None else terms.maturity_date

        if cycles:
            timestamps = resolve_array_schedule(
                anchors,
                cycles,
                effective_end,
                end_of_month_convention=contract.end_of_month_convention,
                business_day_convention=contract.business_day_convention,
                calendar=contract.calendar,
            )
        else:
            timestamps = tuple(anchor for anchor in anchors)
        return tuple(
            ts
            for ts in deduplicate_timestamps(timestamps)
            if terms.initial_exchange_date < ts <= effective_end
        )

    anchor = contract.principal_redemption_anchor
    cycle = contract.principal_redemption_cycle

    # Use provided end_date or fall back to terms.maturity_date
    effective_end = end_date if end_date is not None else terms.maturity_date

    if anchor is None or cycle is None or effective_end is None:
        return ()

    # Parse cycle to access stub attribute
    parsed_cycle = Cycle.parse_cycle(cycle)

    timestamps = resolve_cycle_schedule(
        anchor,
        cycle,
        effective_end,
        end_of_month_convention=contract.end_of_month_convention,
        business_day_convention=contract.business_day_convention,
        calendar=contract.calendar,
    )
    if parsed_cycle.stub == "+" and timestamps:
        if timestamps[-1] != effective_end:
            timestamps = timestamps[:-1]
    return tuple(
        ts for ts in timestamps if terms.initial_exchange_date <= ts < effective_end
    )


def resolve_interest_schedule(
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
        >>> schedule = resolve_interest_schedule(contract, terms)
        # Returns timestamps: [Feb 1, Mar 1, ..., Dec 1, Jan 1 2022]
    """
    anchor = contract.interest_payment_anchor
    cycle = contract.interest_payment_cycle
    if anchor is None or cycle is None or terms.maturity_date is None:
        return ()

    # Parse cycle to access stub attribute
    parsed_cycle = Cycle.parse_cycle(cycle)

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
            if parsed_cycle.stub == "+":
                timestamps[-1] = maturity_date
            else:
                timestamps.append(maturity_date)
    return tuple(deduplicate_timestamps(timestamps))


def resolve_rate_reset_occurrences(
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


def resolve_ipcb_schedule(
    contract: ContractAttributes,
    maturity_date: int | None,
) -> tuple[int, ...]:
    """
    Resolve IPCB (Interest Payment Calculation Base) occurrence schedule.

    Args:
        contract: ACTUS contract attributes.
        maturity_date: Contract maturity date.

    Returns:
        Tuple of timestamps for IPCB events.
    """
    anchor = contract.interest_calculation_base_anchor
    cycle = contract.interest_calculation_base_cycle
    if anchor is None or cycle is None or maturity_date is None:
        return ()
    return tuple(
        ts
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
