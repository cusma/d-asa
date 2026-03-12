from typing import TypeAlias

from algopy import Asset, UInt64, arc4

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
