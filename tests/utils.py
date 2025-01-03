import math
from dataclasses import asdict, dataclass
from typing import Optional, TypeAlias

from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner, TransactionSigner
from algokit_utils.beta.algorand_client import AlgorandClient, PayParams
from algosdk.abi import TupleType, UintType
from algosdk.constants import min_txn_fee
from algosdk.encoding import decode_address
from algosdk.transaction import SuggestedParams
from algosdk.v2client.algod import AlgodClient

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient

COUPON_PER_OP_UP_TXN = 10  # This parameter is empirical and depends on the complexity of `count_due_coupons` subroutine

CouponRates: TypeAlias = list[int]
TimeEvents: TypeAlias = list[int]
TimePeriods: TypeAlias = list[tuple[int, int]]


@dataclass
class DAsaConfig:
    denomination_asset_id: int
    principal: int
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
class DAsaAccountManager(AddressAndSigner):
    @classmethod
    def role_box_prefix(cls) -> bytes:
        return sc_cst.PREFIX_BOX_ID_ACCOUNT_MANAGER

    @classmethod
    def role_id(cls) -> int:
        return sc_cst.ROLE_ACCOUNT_MANAGER

    @classmethod
    def box_id_from_address(cls, address: str) -> bytes:
        return cls.role_box_prefix() + decode_address(address)

    @property
    def box_id(self) -> bytes:
        return self.role_box_prefix() + decode_address(self.address)


@dataclass(kw_only=True)
class DAsaPrimaryDealer(AddressAndSigner):
    @classmethod
    def role_box_prefix(cls) -> bytes:
        return sc_cst.PREFIX_BOX_ID_PRIMARY_DEALER

    @classmethod
    def role_id(cls) -> int:
        return sc_cst.ROLE_PRIMARY_DEALER

    @classmethod
    def box_id_from_address(cls, address: str) -> bytes:
        return cls.role_box_prefix() + decode_address(address)

    @property
    def box_id(self) -> bytes:
        return self.role_box_prefix() + decode_address(self.address)


@dataclass(kw_only=True)
class DAsaTrustee(AddressAndSigner):
    @classmethod
    def role_box_prefix(cls) -> bytes:
        return sc_cst.PREFIX_BOX_ID_TRUSTEE

    @classmethod
    def role_id(cls) -> int:
        return sc_cst.ROLE_TRUSTEE

    @classmethod
    def box_id_from_address(cls, address: str) -> bytes:
        return cls.role_box_prefix() + decode_address(address)

    @property
    def box_id(self) -> bytes:
        return self.role_box_prefix() + decode_address(self.address)


@dataclass(kw_only=True)
class DAsaAuthority(AddressAndSigner):
    @classmethod
    def role_box_prefix(cls) -> bytes:
        return sc_cst.PREFIX_BOX_ID_AUTHORITY

    @classmethod
    def role_id(cls) -> int:
        return sc_cst.ROLE_AUTHORITY

    @classmethod
    def box_id_from_address(cls, address: str) -> bytes:
        return cls.role_box_prefix() + decode_address(address)

    @property
    def box_id(self) -> bytes:
        return self.role_box_prefix() + decode_address(self.address)


@dataclass(kw_only=True)
class DAsaInterestOracle(AddressAndSigner):
    @classmethod
    def role_box_prefix(cls) -> bytes:
        return sc_cst.PREFIX_BOX_ID_INTEREST_ORACLE

    @classmethod
    def role_id(cls) -> int:
        return sc_cst.ROLE_INTEREST_ORACLE

    @classmethod
    def box_id_from_address(cls, address: str) -> bytes:
        return cls.role_box_prefix() + decode_address(address)

    @property
    def box_id(self) -> bytes:
        return self.role_box_prefix() + decode_address(self.address)


@dataclass(kw_only=True)
class DAsaAccount:
    holding_address: str
    signer: TransactionSigner
    d_asa_client: BaseDAsaClient

    @classmethod
    def role_box_prefix(cls) -> bytes:
        return sc_cst.PREFIX_BOX_ID_ACCOUNT

    @classmethod
    def box_id_from_address(cls, address: str) -> bytes:
        return cls.role_box_prefix() + decode_address(address)

    @property
    def box_id(self) -> bytes:
        return self.role_box_prefix() + decode_address(self.holding_address)

    @property
    def payment_address(self) -> str:
        return self.d_asa_client.get_account_info(
            holding_address=self.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(self.d_asa_client.app_id, self.box_id)]
            ),
        ).return_value.payment_address

    @property
    def units(self) -> int:
        return self.d_asa_client.get_account_info(
            holding_address=self.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(self.d_asa_client.app_id, self.box_id)]
            ),
        ).return_value.units

    @property
    def unit_value(self) -> int:
        return self.d_asa_client.get_account_info(
            holding_address=self.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(self.d_asa_client.app_id, self.box_id)]
            ),
        ).return_value.unit_value

    @property
    def paid_coupons(self) -> int:
        return self.d_asa_client.get_account_info(
            holding_address=self.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(self.d_asa_client.app_id, self.box_id)]
            ),
        ).return_value.paid_coupons

    @property
    def suspended(self) -> bool:
        return self.d_asa_client.get_account_info(
            holding_address=self.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(self.d_asa_client.app_id, self.box_id)]
            ),
        ).return_value.suspended

    @property
    def principal(self) -> int:
        return self.units * self.unit_value


def get_last_round(algod_client: AlgodClient) -> int:
    return algod_client.status()["last-round"]  # type: ignore


def get_latest_timestamp(algod_client: AlgodClient) -> int:
    return algod_client.block_info(get_last_round(algod_client))["block"]["ts"]  # type: ignore


def round_warp(to_round: Optional[int] = None) -> None:
    """
    Fastforward directly `to_round` or advance by 1 round.

    Args:
        to_round (Optional): Round to advance to
    """
    algorand_client = AlgorandClient.default_local_net()
    algorand_client.set_suggested_params_timeout(0)
    dispenser = algorand_client.account.localnet_dispenser()
    if to_round is not None:
        last_round = get_last_round(algorand_client.client.algod)
        assert to_round > last_round
        n_rounds = to_round - last_round
    else:
        n_rounds = 1
    for _ in range(n_rounds):
        algorand_client.send.payment(
            PayParams(
                signer=dispenser.signer,
                sender=dispenser.address,
                receiver=dispenser.address,
                amount=0,
            )
        )


def time_warp(to_timestamp: int) -> None:
    """
    Fastforward directly `to_timestamp`

    Args:
        to_timestamp: Timestamp to advance to
    """
    algorand_client = AlgorandClient.default_local_net()
    algorand_client.set_suggested_params_timeout(0)
    algorand_client.client.algod.set_timestamp_offset(
        to_timestamp - get_latest_timestamp(algorand_client.client.algod)
    )
    round_warp()
    algorand_client.client.algod.set_timestamp_offset(0)


def sp_per_coupon(coupon_idx: int) -> SuggestedParams:
    """
    Set fee credit for opcode budget, based on coupon index to process

    Args:
        coupon_idx: coupon index to process

    Returns:

    """
    algorand_client = AlgorandClient.default_local_net()
    sp = algorand_client.get_suggested_params()
    sp.flat_fee = True
    sp.fee = math.ceil(coupon_idx / COUPON_PER_OP_UP_TXN) * min_txn_fee
    return sp


def set_role_config(validity_start: int = 0, validity_end: int = 2**64 - 1) -> bytes:
    return TupleType([UintType(64), UintType(64)]).encode(
        [validity_start, validity_end]
    )
