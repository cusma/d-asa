"""Contract-type specific schedule builders for ACTUS normalization."""

from __future__ import annotations

from smart_contracts import constants as cst
from smart_contracts import enums

from ..contracts import ContractAttributes
from ..errors import ActusNormalizationError
from ..models import NormalizedActusTerms
from .calculations import (
    calculate_interest,
    calculate_principal_payment,
    interpolate_balance_at_timestamp,
)
from .conversions import rate_to_fp, to_asa_units
from .event_seeds import EventSeed, create_seed
from .schedules import (
    resolve_interest_schedule,
    resolve_ipcb_schedule,
    resolve_principal_schedule,
    resolve_rate_reset_occurrences,
)


def build_ied_seed(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
) -> EventSeed:
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
    from .core import get_initial_next_principal_redemption

    return EventSeed(
        event_type="IED",
        scheduled_time=terms.initial_exchange_date,
        next_nominal_interest_rate=rate_to_fp(contract.nominal_interest_rate),
        next_principal_redemption=get_initial_next_principal_redemption(
            contract, terms, asa_decimals
        ),
        next_outstanding_principal=terms.notional_principal,
        flags=enums.FLAG_NON_CASH_EVENT,
    )


def build_rate_reset_seeds(
    contract: ContractAttributes,
    outstanding: int,
    maturity_date: int | None,
    next_rate_fp: int,
) -> tuple[EventSeed, ...]:
    """
    Build non-cash RR/RRF event seeds from the rate reset schedule.

    Creates RR (Rate Reset) and RRF (Rate Reset with Fixed spread) event seeds
    that update the interest rate without cash flows.

    Args:
        contract: ACTUS contract attributes.
        outstanding: Current outstanding principal.
        maturity_date: Contract maturity date.
        next_rate_fp: Next rate in fixed-point representation.

    Returns:
        Tuple of rate reset event seeds.
    """
    if maturity_date is None:
        return ()
    return tuple(
        create_seed(
            ts,
            event_type=event_type,
            next_nominal_interest_rate=next_rate_fp if event_type == "RRF" else 0,
            next_outstanding_principal=outstanding,
            flags=enums.FLAG_NON_CASH_EVENT,
        )
        for ts, event_type in resolve_rate_reset_occurrences(contract, maturity_date)
    )


def build_ipcb_seeds(
    contract: ContractAttributes,
    outstanding: int,
    maturity_date: int | None,
) -> tuple[EventSeed, ...]:
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
    return tuple(
        create_seed(
            ts,
            event_type="IPCB",
            next_outstanding_principal=outstanding,
            flags=enums.FLAG_NON_CASH_EVENT,
        )
        for ts in resolve_ipcb_schedule(contract, maturity_date)
    )


def build_pam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms
) -> tuple[EventSeed, ...]:
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

    seeds: list[EventSeed] = []
    outstanding = terms.notional_principal

    for ts in resolve_interest_schedule(contract, terms):
        seeds.append(
            create_seed(
                ts,
                event_type="IP",
                next_outstanding_principal=outstanding,
                flags=enums.FLAG_CASH_EVENT,
            )
        )

    next_rate = rate_to_fp(
        contract.rate_reset_next
        if contract.rate_reset_next is not None
        else contract.nominal_interest_rate
    )
    seeds.extend(
        build_rate_reset_seeds(contract, outstanding, terms.maturity_date, next_rate)
    )

    seeds.append(
        create_seed(
            terms.maturity_date,
            event_type="MD",
            next_outstanding_principal=0,
            flags=enums.FLAG_CASH_EVENT,
        )
    )
    return tuple(seeds)


def build_clm_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms
) -> tuple[EventSeed, ...]:
    """
    Build the normalized CLM (Call Money) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.

    Returns:
        Tuple of event seeds for the CLM schedule.
    """
    seeds: list[EventSeed] = []
    outstanding = terms.notional_principal

    if terms.maturity_date is not None:
        for ts in resolve_interest_schedule(contract, terms):
            seeds.append(
                create_seed(
                    ts,
                    event_type="IP",
                    next_outstanding_principal=outstanding,
                    flags=enums.FLAG_CASH_EVENT,
                )
            )
        seeds.append(
            create_seed(
                terms.maturity_date,
                event_type="MD",
                next_outstanding_principal=0,
                flags=enums.FLAG_CASH_EVENT,
            )
        )

    next_rate = rate_to_fp(
        contract.rate_reset_next
        if contract.rate_reset_next is not None
        else contract.nominal_interest_rate
    )
    seeds.extend(
        build_rate_reset_seeds(contract, outstanding, terms.maturity_date, next_rate)
    )
    return tuple(seeds)


def build_lam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[EventSeed, ...]:
    """
    Build the normalized LAM (Linear Amortizer) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the LAM schedule.
    """
    return build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=False, lax=False
    )


def build_nam_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[EventSeed, ...]:
    """
    Build the normalized NAM (Negative Amortizer) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the NAM schedule.
    """
    return build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=True, lax=False
    )


def build_lax_schedule(
    contract: ContractAttributes, terms: NormalizedActusTerms, asa_decimals: int
) -> tuple[EventSeed, ...]:
    """
    Build the normalized LAX (Linear Amortizer with eXtensions) event seed schedule.

    Args:
        contract: ACTUS contract attributes.
        terms: Normalized contract terms.
        asa_decimals: Decimal places for the denomination ASA.

    Returns:
        Tuple of event seeds for the LAX schedule.
    """
    return build_amortizing_schedule(
        contract, terms, asa_decimals, allow_negative=True, lax=True
    )


def get_lax_direction(contract: ContractAttributes, period_index: int) -> str:
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


def build_amortizing_schedule(
    contract: ContractAttributes,
    terms: NormalizedActusTerms,
    asa_decimals: int,
    *,
    allow_negative: bool,
    lax: bool,
) -> tuple[EventSeed, ...]:
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

    seeds: list[EventSeed] = []
    outstanding = terms.notional_principal
    rate_fp = rate_to_fp(contract.nominal_interest_rate)
    pr_schedule = resolve_principal_schedule(contract, terms, lax=lax)
    if not pr_schedule:
        raise ActusNormalizationError(
            f"{contract_type} normalization requires a principal redemption schedule"
        )

    payment_total = to_asa_units(
        contract.next_principal_redemption_amount or 0,
        asa_decimals,
    )

    # Precompute LAX principal amounts once
    pr_values_scaled: tuple[int, ...] | None = None
    if lax and contract.array_pr_next is not None:
        pr_values_scaled = tuple(
            to_asa_units(value, asa_decimals) for value in contract.array_pr_next
        )

    # Build rate reset schedule as dict for efficient lookup
    rr_schedule = resolve_rate_reset_occurrences(contract, terms.maturity_date)
    rr_events = dict(rr_schedule)
    next_rate = rate_to_fp(
        contract.rate_reset_next
        if contract.rate_reset_next is not None
        else contract.nominal_interest_rate
    )

    previous_due = terms.initial_exchange_date
    # Track balance timeline for interpolation
    balance_timeline: list[tuple[int, int]] = []

    for index, ts in enumerate(pr_schedule):
        due_time = ts
        interest_due = calculate_interest(
            principal=outstanding,
            rate_fp=rate_fp,
            start_ts=previous_due,
            end_ts=due_time,
            day_count_convention=terms.day_count_convention,
            maturity_date=terms.maturity_date,
        )
        principal_payment, payment_total = calculate_principal_payment(
            outstanding=outstanding,
            payment_total=payment_total,
            interest_due=interest_due,
            allow_negative=allow_negative,
            annuity=False,
            lax=lax,
            period_index=index,
            pr_values_scaled=pr_values_scaled,
        )
        lax_direction = get_lax_direction(contract, index) if lax else "DEC"

        # For NAM, negative principal_payment means capitalization (increase outstanding)
        # For other types, subtract principal_payment from outstanding
        if allow_negative and not lax:
            # NAM: negative principal_payment increases outstanding (capitalization)
            next_outstanding = outstanding - principal_payment
            # Validate that capitalization doesn't cause uint64 overflow
            if next_outstanding < 0 or next_outstanding > cst.MAX_UINT64:
                raise ActusNormalizationError(
                    f"NAM capitalization at period {index} would result in outstanding principal "
                    f"{next_outstanding} which exceeds uint64 bounds (0 to {cst.MAX_UINT64}). "
                    f"Outstanding: {outstanding}, principal_payment: {principal_payment}"
                )
        else:
            # LAM/LAX: always decrease or maintain outstanding
            next_outstanding = max(outstanding - principal_payment, 0)

        if lax_direction == "INC":
            next_outstanding = outstanding + payment_total

        # Record balance change
        balance_timeline.append((ts, next_outstanding))

        # For NAM with negative principal_payment (capitalization), still generate PR event
        # For LAM/LAX, only generate events if principal_payment > 0
        if principal_payment > 0 or (allow_negative and not lax):
            # For LAX INC periods, generate PI (Principal Increase) events
            if lax and lax_direction == "INC":
                seeds.append(
                    create_seed(
                        ts,
                        event_type="PI",
                        next_principal_redemption=payment_total,
                        next_outstanding_principal=next_outstanding,
                        flags=enums.FLAG_NON_CASH_EVENT,
                    )
                )
            else:
                # Normal redemption or DEC periods generate PR events
                # For NAM with negative principal_payment, this is a cash event (payment made)
                # but outstanding increases due to capitalization
                seeds.append(
                    create_seed(
                        ts,
                        event_type="PR",
                        next_principal_redemption=payment_total,
                        next_outstanding_principal=next_outstanding,
                        flags=enums.FLAG_CASH_EVENT,
                    )
                )
        elif lax:
            # For LAX with zero principal_payment, still respect direction
            if lax_direction == "INC":
                seeds.append(
                    create_seed(
                        ts,
                        event_type="PI",
                        next_principal_redemption=payment_total,
                        next_outstanding_principal=next_outstanding,
                        flags=enums.FLAG_NON_CASH_EVENT,
                    )
                )
            else:  # DEC
                seeds.append(
                    create_seed(
                        ts,
                        event_type="PR",
                        next_principal_redemption=payment_total,
                        next_outstanding_principal=next_outstanding,
                        flags=enums.FLAG_NON_CASH_EVENT,
                    )
                )

        if interest_due > 0 or due_time == terms.maturity_date:
            seeds.append(
                create_seed(
                    ts,
                    event_type="IP",
                    next_principal_redemption=payment_total,
                    next_outstanding_principal=next_outstanding,
                    flags=enums.FLAG_CASH_EVENT,
                )
            )

        # Check if this timestamp has a rate reset event
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

    # Add remaining rate reset events that don't coincide with PR dates
    for ts, event_type in rr_schedule:
        if any(ts == pr_ts for pr_ts in pr_schedule):
            continue
        if ts >= terms.maturity_date:
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

    seeds.extend(build_ipcb_seeds(contract, outstanding, terms.maturity_date))
    if outstanding:
        seeds.append(
            create_seed(
                terms.maturity_date,
                event_type="MD",
                next_principal_redemption=payment_total,
                next_outstanding_principal=0,
                flags=enums.FLAG_CASH_EVENT,
            )
        )
    return tuple(seeds)
