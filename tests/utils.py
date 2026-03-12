import math
from base64 import b64decode
from dataclasses import asdict, dataclass
from typing import Any, TypeAlias

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    PaymentParams,
    SendAppTransactionResult,
    SigningAccount,
)
from algosdk.constants import min_txn_fee
from algosdk.v2client.algod import AlgodClient

from smart_contracts import enums
from smart_contracts.artifacts.d_asa.dasa_client import (
    AccountGetPositionArgs,
)

COUPON_PER_OP_UP_TXN = 10  # This parameter is empirical and depends on the complexity of `count_due_coupons` subroutine

CouponRates: TypeAlias = list[int]
TimeEvents: TypeAlias = list[int]
TimePeriods: TypeAlias = list[tuple[int, int]]


@dataclass
class DAsaConfig:
    denomination_asset_id: int
    settlement_asset_id: int
    principal: int
    principal_discount: int
    minimum_denomination: int
    day_count_convention: int
    interest_rate: int
    coupon_rates: CouponRates
    time_events: TimeEvents
    time_periods: TimePeriods

    def dictify(self) -> dict[str, int | CouponRates | TimeEvents | TimePeriods]:
        return asdict(self)  # type: ignore

    @property
    def total_coupons(self) -> int:
        return len(self.coupon_rates)


@dataclass
class Currency:
    id: int
    total: int
    decimals: int
    name: str
    unit_name: str
    asa_to_unit: float


@dataclass(kw_only=True)
class DAsaAccountManager(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_ACCOUNT_MANAGER


@dataclass(kw_only=True)
class DAsaPrimaryDealer(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_PRIMARY_DEALER


@dataclass(kw_only=True)
class DAsaTrustee(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_TRUSTEE


@dataclass(kw_only=True)
class DAsaAuthority(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_AUTHORITY


@dataclass(kw_only=True)
class DAsaInterestOracle(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_OBSERVER


@dataclass(kw_only=True)
class DAsaAccount(SigningAccount):
    holding_address: str
    d_asa_client: Any

    @property
    def payment_address(self) -> str:
        return self.d_asa_client.send.account_get_position(
            AccountGetPositionArgs(
                holding_address=self.holding_address,
            )
        ).abi_return.payment_address

    @property
    def units(self) -> int:
        return self.d_asa_client.send.account_get_position(
            AccountGetPositionArgs(holding_address=self.holding_address)
        ).abi_return.units

    @property
    def suspended(self) -> bool:
        return self.d_asa_client.send.account_get_position(
            AccountGetPositionArgs(holding_address=self.holding_address)
        ).abi_return.suspended


def get_last_round(algod_client: AlgodClient) -> int:
    return algod_client.status()["last-round"]  # type: ignore


def get_latest_timestamp(algod_client: AlgodClient) -> int:
    return algod_client.block_info(get_last_round(algod_client))["block"]["ts"]  # type: ignore


def round_warp(to_round: int | None = None) -> None:
    """
    Fastforward directly `to_round` or advance by 1 round.

    Args:
        to_round (Optional): Round to advance to
    """
    algorand_client = AlgorandClient.default_localnet()
    algorand_client.set_suggested_params_cache_timeout(0)
    dispenser = algorand_client.account.localnet_dispenser()
    if to_round is not None:
        last_round = get_last_round(algorand_client.client.algod)
        assert to_round > last_round
        n_rounds = to_round - last_round
    else:
        n_rounds = 1
    for _ in range(n_rounds):
        algorand_client.send.payment(
            PaymentParams(
                signer=dispenser.signer,
                sender=dispenser.address,
                receiver=dispenser.address,
                amount=AlgoAmount.from_algo(0),
            )
        )


def time_warp(to_timestamp: int) -> None:
    """
    Fastforward directly `to_timestamp`

    Args:
        to_timestamp: Timestamp to advance to
    """
    algorand_client = AlgorandClient.default_localnet()
    algorand_client.set_suggested_params_cache_timeout(0)
    algorand_client.client.algod.set_timestamp_offset(
        to_timestamp - get_latest_timestamp(algorand_client.client.algod)
    )
    round_warp()
    algorand_client.client.algod.set_timestamp_offset(0)


def max_fee_per_coupon(coupon_idx: int) -> AlgoAmount:
    """
    Compute max fee credit for opcode budget, based on coupon index to process

    Args:
        coupon_idx: coupon index to process

    Returns:
        Max fee
    """
    return AlgoAmount.from_micro_algo(
        math.ceil(coupon_idx / COUPON_PER_OP_UP_TXN) * min_txn_fee
    )


def get_event_from_call_result(call_result: SendAppTransactionResult) -> bytes:
    # Contract emits ACTUS events right before the ARC-4 (which is the last log)
    event = call_result.returns[0].tx_info["logs"][-2]
    # Stripping ARC-28 4-bytes event signature prefix
    event_bytes = b64decode(event)
    return event_bytes[4:]


def decode_actus_event(event_bytes: bytes) -> dict:
    """
    Decode an ACTUS ARC-28 Event from bytes using ARC-4 encoding.

    In ARC-4, structs with dynamic types (String, Bytes) use offsets:
    - Fixed-size fields are stored inline
    - Dynamic fields are stored as 2-byte offsets pointing to data at the end

    Event structure (ARC-4 encoding):
    Fixed part (head):
    - contract_id: UInt64 (8 bytes)
    - type: arc4.UInt8 (1 byte)
    - type_name: offset (2 bytes) -> points to String data in tail
    - time: UInt64 (8 bytes)
    - payoff: UInt64 (8 bytes)
    - currency_id: UInt64 (8 bytes)
    - currency_unit: offset (2 bytes) -> points to Bytes data in tail
    - nominal_value: UInt64 (8 bytes)
    - nominal_rate_bps: arc4.UInt16 (2 bytes)
    - nominal_accrued: UInt64 (8 bytes)

    Dynamic part (tail):
    - String data for type_name (2 bytes length + UTF-8 data)
    - Bytes data for currency_unit (2 bytes length + raw data)

    Args:
        event_bytes: The raw event bytes (after removing the 4-byte event signature)

    Returns:
        Dictionary with decoded event fields
    """
    import struct

    offset = 0

    # Read contract_id (UInt64 - 8 bytes)
    contract_id = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    # Read type (arc4.UInt8 - 1 byte)
    event_type = event_bytes[offset]
    offset += 1

    # Read type_name offset (2 bytes)
    type_name_offset = struct.unpack(">H", event_bytes[offset : offset + 2])[0]
    offset += 2

    # Read time (UInt64 - 8 bytes)
    time = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    # Read payoff (UInt64 - 8 bytes)
    payoff = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    # Read currency_id (UInt64 - 8 bytes)
    currency_id = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    # Read currency_unit offset (2 bytes)
    currency_unit_offset = struct.unpack(">H", event_bytes[offset : offset + 2])[0]
    offset += 2

    # Read nominal_value (UInt64 - 8 bytes)
    nominal_value = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    # Read nominal_rate_bps (arc4.UInt16 - 2 bytes)
    nominal_rate_bps = struct.unpack(">H", event_bytes[offset : offset + 2])[0]
    offset += 2

    # Read nominal_accrued (UInt64 - 8 bytes)
    nominal_accrued = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    # Now decode the dynamic fields using their offsets
    # Read type_name from tail
    type_name_length = struct.unpack(
        ">H", event_bytes[type_name_offset : type_name_offset + 2]
    )[0]
    type_name = event_bytes[
        type_name_offset + 2 : type_name_offset + 2 + type_name_length
    ].decode("utf-8")

    # Read currency_unit from tail
    currency_unit_length = struct.unpack(
        ">H", event_bytes[currency_unit_offset : currency_unit_offset + 2]
    )[0]
    currency_unit = event_bytes[
        currency_unit_offset + 2 : currency_unit_offset + 2 + currency_unit_length
    ].decode("utf-8")

    return {
        "contract_id": contract_id,
        "type": event_type,
        "type_name": type_name,
        "time": time,
        "payoff": payoff,
        "currency_id": currency_id,
        "currency_unit": currency_unit,
        "nominal_value": nominal_value,
        "nominal_rate_bps": nominal_rate_bps,
        "nominal_accrued": nominal_accrued,
    }


def decode_actus_execution_event(event_bytes: bytes) -> dict[str, int]:
    import struct

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
    ) = struct.unpack(">QQBQQQBQQQ", event_bytes)

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
