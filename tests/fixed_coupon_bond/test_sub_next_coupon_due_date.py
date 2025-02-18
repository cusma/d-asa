from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaConfig, max_fee_per_coupon, time_warp

TIME_LEFT_TO_DUE_DATE = 100  # Seconds


def test_next_coupon_due_date_before_issuance(
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_primary.send.get_time_events().abi_return
    next_coupon_due_date = (
        fixed_coupon_bond_client_primary.send.get_coupons_status().abi_return.next_coupon_due_date
    )
    assert next_coupon_due_date == time_events[sc_cfg.FIRST_COUPON_DATE_IDX]


def test_next_coupon_due_date_ongoing(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_ongoing.send.get_time_events().abi_return
    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date - TIME_LEFT_TO_DUE_DATE)
        next_coupon_due_date = fixed_coupon_bond_client_ongoing.send.get_coupons_status(
            params=CommonAppCallParams(
                max_fee=max_fee_per_coupon(fixed_coupon_bond_cfg.total_coupons)
            ),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        ).abi_return.next_coupon_due_date
        print("Next coupon due date: ", next_coupon_due_date)
        assert next_coupon_due_date == coupon_due_date


def test_next_coupon_due_date_at_maturity(
    fixed_coupon_bond_client_at_maturity: FixedCouponBondClient,
) -> None:
    next_coupon_due_date = (
        fixed_coupon_bond_client_at_maturity.send.get_coupons_status().abi_return.next_coupon_due_date
    )
    assert next_coupon_due_date == 0
