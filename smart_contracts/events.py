from typing import TypeAlias

from algopy import Bytes, String, UInt64, arc4

Timestamp: TypeAlias = UInt64


class Event(arc4.Struct, kw_only=True):
    """ACTUS Event."""

    contract_id: UInt64
    type: arc4.UInt8
    type_name: String
    time: Timestamp
    payoff: UInt64
    currency_id: UInt64
    currency_unit: Bytes
    nominal_value: UInt64
    nominal_rate_bps: arc4.UInt16
    nominal_accrued: UInt64
