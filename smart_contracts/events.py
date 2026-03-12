from typing import TypeAlias

from algopy import Asset, UInt64, arc4
from algosdk.abi import TupleType, UintType

Timestamp: TypeAlias = UInt64


class ExecutionEvent(arc4.Struct, kw_only=True):
    """Non-normative receipt for on-chain execution of a scheduled ACTUS event."""

    contract_id: UInt64
    event_id: UInt64
    event_type: arc4.UInt8
    scheduled_time: Timestamp
    applied_at: Timestamp
    payoff: UInt64
    payoff_sign: arc4.UInt8
    settled_amount: UInt64
    currency_id: Asset
    sequence: UInt64


_ACTUS_EXECUTION_EVENT_TUPLE = TupleType(
    [
        UintType(64),
        UintType(64),
        UintType(8),
        UintType(64),
        UintType(64),
        UintType(64),
        UintType(8),
        UintType(64),
        UintType(64),
        UintType(64),
    ]
)


def decode_actus_execution_event(event_bytes: bytes) -> dict[str, int]:
    """Decode the ARC-28 payload emitted for an ACTUS schedule transition."""
    (
        contract_id,
        event_id,
        event_type,
        scheduled_time,
        applied_at,
        payoff,
        payoff_sign,
        settled_amount,
        currency_id,
        sequence,
    ) = _ACTUS_EXECUTION_EVENT_TUPLE.decode(event_bytes)
    return {
        "contract_id": contract_id,
        "event_id": event_id,
        "event_type": event_type,
        "scheduled_time": scheduled_time,
        "applied_at": applied_at,
        "payoff": payoff,
        "payoff_sign": payoff_sign,
        "settled_amount": settled_amount,
        "currency_id": currency_id,
        "sequence": sequence,
    }
