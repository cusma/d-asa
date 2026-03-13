from __future__ import annotations

from .artifacts.dasa_client import (
    AccountPosition as _ClientAccountPosition,
)
from .artifacts.dasa_client import (
    InitialKernelState as _ClientInitialKernelState,
)
from .artifacts.dasa_client import (
    NormalizedActusTerms as _ClientNormalizedActusTerms,
)
from .artifacts.dasa_client import (
    ObservedCashEventRequest as _ClientObservedCashEventRequest,
)
from .artifacts.dasa_client import (
    ObservedEventRequest as _ClientObservedEventRequest,
)
from .artifacts.dasa_client import (
    Prospectus as _ClientProspectus,
)
from .artifacts.dasa_client import (
    RoleValidity as _ClientRoleValidity,
)
from .models import (
    AccountPosition,
    ExecutionScheduleEntry,
    NormalizationResult,
    ObservedCashEventRequest,
    ObservedEventRequest,
)
from .registry import EVENT_TYPE_IDS


def to_client_terms(result: NormalizationResult) -> _ClientNormalizedActusTerms:
    return _ClientNormalizedActusTerms(
        contract_type=result.terms.contract_type,
        denomination_asset_id=result.terms.denomination_asset_id,
        settlement_asset_id=result.terms.denomination_asset_id,
        total_units=result.terms.total_units,
        notional_principal=result.terms.notional_principal,
        initial_exchange_amount=result.terms.initial_exchange_amount,
        initial_exchange_date=result.terms.initial_exchange_date,
        maturity_date=result.terms.maturity_date or 0,
        day_count_convention=int(result.terms.day_count_convention),
        rate_reset_spread=result.terms.rate_reset_spread,
        rate_reset_multiplier=result.terms.rate_reset_multiplier,
        rate_reset_floor=result.terms.rate_reset_floor,
        rate_reset_cap=result.terms.rate_reset_cap,
        rate_reset_next=result.terms.rate_reset_next,
        has_rate_reset_floor=result.terms.has_rate_reset_floor,
        has_rate_reset_cap=result.terms.has_rate_reset_cap,
        dynamic_principal_redemption=result.terms.dynamic_principal_redemption,
        fixed_point_scale=result.terms.fixed_point_scale,
    )


def to_client_initial_state(result: NormalizationResult) -> _ClientInitialKernelState:
    return _ClientInitialKernelState(
        status_date=result.initial_state.status_date,
        event_cursor=result.initial_state.event_cursor,
        outstanding_principal=result.initial_state.outstanding_principal,
        interest_calculation_base=result.initial_state.interest_calculation_base,
        nominal_interest_rate=result.initial_state.nominal_interest_rate,
        accrued_interest=result.initial_state.accrued_interest,
        next_principal_redemption=result.initial_state.next_principal_redemption,
        cumulative_interest_index=result.initial_state.cumulative_interest_index,
        cumulative_principal_index=result.initial_state.cumulative_principal_index,
    )


def to_client_schedule_page(
    page: tuple[ExecutionScheduleEntry, ...],
) -> list[tuple[int, int, int, int, int, int, int, int, int]]:
    return [
        (
            entry.event_id,
            EVENT_TYPE_IDS[entry.event_type],
            entry.scheduled_time,
            entry.accrual_factor,
            entry.redemption_accrual_factor,
            entry.next_nominal_interest_rate,
            entry.next_principal_redemption,
            entry.next_outstanding_principal,
            entry.flags,
        )
        for entry in page
    ]


def to_client_prospectus(
    *,
    url: str = "",
    hash_bytes: bytes | None = None,
) -> _ClientProspectus:
    raw_hash = hash_bytes or bytes(32)
    if len(raw_hash) != 32:
        raise ValueError("prospectus hash must be exactly 32 bytes")
    return _ClientProspectus(hash=raw_hash, url=url)


def to_sdk_account_position(
    position: AccountPosition | _ClientAccountPosition,
) -> AccountPosition:
    if isinstance(position, AccountPosition):
        return position
    return AccountPosition(
        units=position.units,
        reserved_units=position.reserved_units,
        payment_address=position.payment_address,
        suspended=position.suspended,
        settled_cursor=position.settled_cursor,
        interest_checkpoint=position.interest_checkpoint,
        principal_checkpoint=position.principal_checkpoint,
        claimable_interest=position.claimable_interest,
        claimable_principal=position.claimable_principal,
    )


def to_sdk_schedule_entry(
    entry: ExecutionScheduleEntry | tuple[int, int, int, int, int, int, int, int, int],
) -> ExecutionScheduleEntry:
    if isinstance(entry, ExecutionScheduleEntry):
        return entry
    (
        event_id,
        event_type,
        scheduled_time,
        accrual_factor,
        redemption_accrual_factor,
        next_nominal_interest_rate,
        next_principal_redemption,
        next_outstanding_principal,
        flags,
    ) = entry
    event_type_names = {value: name for name, value in EVENT_TYPE_IDS.items()}
    if event_type not in event_type_names:
        raise ValueError(f"unsupported event type id: {event_type}")
    return ExecutionScheduleEntry(
        event_id=event_id,
        event_type=event_type_names[event_type],
        scheduled_time=scheduled_time,
        accrual_factor=accrual_factor,
        redemption_accrual_factor=redemption_accrual_factor,
        next_nominal_interest_rate=next_nominal_interest_rate,
        next_principal_redemption=next_principal_redemption,
        next_outstanding_principal=next_outstanding_principal,
        flags=flags,
    )


def to_client_observed_event(
    payload: ObservedEventRequest,
    *,
    event_id: int,
) -> _ClientObservedEventRequest:
    return _ClientObservedEventRequest(
        event_id=event_id,
        event_type=EVENT_TYPE_IDS[payload.event_type],
        scheduled_time=payload.scheduled_time,
        accrual_factor=payload.accrual_factor,
        redemption_accrual_factor=payload.redemption_accrual_factor,
        observed_rate=payload.observed_rate,
        next_nominal_interest_rate=payload.next_nominal_interest_rate,
        next_principal_redemption=payload.next_principal_redemption,
        next_outstanding_principal=payload.next_outstanding_principal,
        flags=payload.flags,
    )


def to_client_observed_cash_event(
    payload: ObservedCashEventRequest,
    *,
    event_id: int,
) -> _ClientObservedCashEventRequest:
    return _ClientObservedCashEventRequest(
        event_id=event_id,
        event_type=EVENT_TYPE_IDS[payload.event_type],
        scheduled_time=payload.scheduled_time,
        accrual_factor=payload.accrual_factor,
        redemption_accrual_factor=payload.redemption_accrual_factor,
        next_nominal_interest_rate=payload.next_nominal_interest_rate,
        next_principal_redemption=payload.next_principal_redemption,
        next_outstanding_principal=payload.next_outstanding_principal,
        flags=payload.flags,
    )


def to_client_role_validity(
    *,
    start: int,
    end: int,
) -> _ClientRoleValidity:
    return _ClientRoleValidity(
        role_validity_start=start,
        role_validity_end=end,
    )
