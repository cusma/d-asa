from algokit_utils import AlgorandClient, SigningAccount

from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from tests.utils import DAsaConfig, time_warp

from .conftest import DUE_COUPONS


def test_count_due_coupons_before_issuance(
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    due_coupons = (
        perpetual_bond_client_primary.send.get_coupons_status().abi_return.due_coupons
    )
    assert due_coupons == 0


def test_count_due_coupons_ongoing(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_ongoing.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    for coupon in range(1, DUE_COUPONS + 1):
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)
        due_coupons = (
            perpetual_bond_client_ongoing.send.get_coupons_status().abi_return.due_coupons
        )
        print("Due coupons: ", due_coupons)
        assert due_coupons == coupon
