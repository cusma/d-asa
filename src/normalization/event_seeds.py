"""Event seed management for ACTUS contract normalization."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from ..models import ExecutionScheduleEntry, ObservedEventRequest
from ..registry import EVENT_SCHEDULE_PRIORITY
from ..unix_time import UTCTimeStamp


@dataclass(frozen=True, slots=True)
class EventSeed:
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


def create_seed(
    timestamp: UTCTimeStamp,
    *,
    event_type: str,
    redemption_accrual_start: UTCTimeStamp = 0,
    redemption_accrual_end: UTCTimeStamp = 0,
    next_nominal_interest_rate: int = 0,
    next_principal_redemption: int = 0,
    next_outstanding_principal: int = 0,
    flags: int = 0,
) -> EventSeed:
    """
    Create an intermediate event seed from a resolved schedule timestamp.

    Factory function for creating EventSeed instances with default values
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
    return EventSeed(
        event_type=event_type,
        scheduled_time=timestamp,
        redemption_accrual_start=redemption_accrual_start,
        redemption_accrual_end=redemption_accrual_end,
        next_nominal_interest_rate=next_nominal_interest_rate,
        next_principal_redemption=next_principal_redemption,
        next_outstanding_principal=next_outstanding_principal,
        flags=flags,
    )


def seed_from_preprocessed(
    event_id: int, item: ObservedEventRequest | ExecutionScheduleEntry
) -> EventSeed:
    """
    Convert a preprocessed event payload into an intermediate event seed.

    Handles both ObservedEventRequest and ExecutionScheduleEntry types,
    converting them to the internal EventSeed representation.

    Args:
        event_id: Unique identifier for the event.
        item: Preprocessed event or schedule entry.

    Returns:
        Event seed representation of the preprocessed event.
    """
    if isinstance(item, ExecutionScheduleEntry):
        return EventSeed(
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
    return seed_from_preprocessed(event_id, entry)


def get_seed_sort_key(seed: EventSeed) -> tuple[int, int, str]:
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


def deduplicate_timestamps(ts: Sequence[UTCTimeStamp]) -> tuple[UTCTimeStamp, ...]:
    """Remove duplicate timestamps while preserving sorted schedule order."""
    return tuple(dict.fromkeys(sorted(ts)))
