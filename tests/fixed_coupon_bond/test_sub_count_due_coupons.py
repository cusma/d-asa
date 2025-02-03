from algokit_utils import SigningAccount

from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaConfig, time_warp


def test_count_due_coupons_before_issuance(
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    due_coupons = (
        fixed_coupon_bond_client_primary.send.get_coupons_status().abi_return.due_coupons
    )
    assert due_coupons == 0


def test_count_due_coupons_ongoing(
    arranger: SigningAccount,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_ongoing.send.get_time_events().abi_return
    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date)
        # FIXME: cover_app_call_inner_transaction_fees seems not working with read-only methods
        # due_coupons = fixed_coupon_bond_client_ongoing.send.get_coupons_status(
        #     params=CommonAppCallParams(max_fee=max_fee_per_coupon(fixed_coupon_bond_cfg.total_coupons)),
        #     send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        # ).abi_return.due_coupons
        # print("Due coupons: ", due_coupons)
        # assert due_coupons == coupon


def test_count_due_coupons_at_maturity(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_at_maturity: FixedCouponBondClient,
) -> None:
    due_coupons = (
        fixed_coupon_bond_client_at_maturity.send.get_coupons_status().abi_return.due_coupons
    )
    assert due_coupons == fixed_coupon_bond_cfg.total_coupons
