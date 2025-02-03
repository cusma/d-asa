from algokit_utils import AlgorandClient

from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    PayCouponArgs,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaAccount, DAsaConfig, time_warp


def test_all_due_coupons_paid(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_ongoing.send.get_time_events().abi_return

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        all_paid = (
            fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.all_due_coupons_paid
        )
        assert all_paid

        # Coupon reaches due date
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date)
        all_paid = (
            fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.all_due_coupons_paid
        )
        assert not all_paid

        # Coupon payment
        fixed_coupon_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=account_a.holding_address,
                payment_info=b"",
            )
        )

        all_paid = (
            fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.all_due_coupons_paid
        )
        assert not all_paid

        fixed_coupon_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=account_b.holding_address,
                payment_info=b"",
            ),
        )
        all_paid = (
            fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.all_due_coupons_paid
        )
        assert all_paid
