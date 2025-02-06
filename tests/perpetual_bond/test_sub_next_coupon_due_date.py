from algokit_utils import AlgorandClient, SigningAccount

from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from tests.utils import DAsaConfig, time_warp

from .conftest import DUE_COUPONS

TIME_LEFT_TO_DUE_DATE = 100  # Seconds


def test_next_coupon_due_date_before_issuance(
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_primary.state.global_state
    next_coupon_due_date = (
        perpetual_bond_client_primary.send.get_coupons_status().abi_return.next_coupon_due_date
    )
    assert next_coupon_due_date == state.issuance_date + state.coupon_period


def test_next_coupon_due_date_ongoing(
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
        time_warp(coupon_due_date - TIME_LEFT_TO_DUE_DATE)
        next_coupon_due_date = (
            perpetual_bond_client_ongoing.send.get_coupons_status().abi_return.next_coupon_due_date
        )
        print("Next coupon due date: ", next_coupon_due_date)
        assert next_coupon_due_date == coupon_due_date
