from typing import Final

from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    GetAccountUnitsCurrentValueArgs,
    GetPaymentAmountArgs,
    PayCouponArgs,
)
from tests.utils import Currency, DAsaAccount, get_latest_timestamp, time_warp

TEST_UNITS: Final[int] = 3

# TODO: Add Actual/Actual DDC tests


def test_from_issuance(
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    current_date = get_latest_timestamp(
        fixed_coupon_bond_client_ongoing.algorand.client.algod
    )
    next_coupon_due_date = (
        fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.next_coupon_due_date
    )
    state = fixed_coupon_bond_client_ongoing.state.global_state
    assert current_date == state.issuance_date

    # Coupon accrued half period
    half_coupon_period = (next_coupon_due_date - current_date) // 2
    time_warp(current_date + half_coupon_period)
    due_coupons = (
        fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.due_coupons
    )
    assert due_coupons == 0

    accrued_interest = (
        fixed_coupon_bond_client_ongoing.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=account_a.units,
            )
        ).abi_return.accrued_interest
    )

    coupon_amount = fixed_coupon_bond_client_ongoing.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account_a.holding_address)
    ).abi_return.interest
    assert accrued_interest == coupon_amount // 2


def test_from_latest_coupon_due_date(
    currency: Currency,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    first_coupon_due_date = (
        fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.next_coupon_due_date
    )
    time_warp(first_coupon_due_date)
    current_date = get_latest_timestamp(
        fixed_coupon_bond_client_ongoing.algorand.client.algod
    )
    assert current_date == first_coupon_due_date
    fixed_coupon_bond_client_ongoing.send.pay_coupon(
        PayCouponArgs(
            holding_address=account_a.holding_address,
            payment_info=b"",
        )
    )

    next_coupon_due_date = (
        fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.next_coupon_due_date
    )

    # Coupon accrued a tenth of period
    tenth_coupon_period = (next_coupon_due_date - current_date) // 10
    time_warp(current_date + tenth_coupon_period)
    due_coupons = (
        fixed_coupon_bond_client_ongoing.send.get_coupons_status().abi_return.due_coupons
    )
    assert due_coupons == 1

    accrued_interest = (
        fixed_coupon_bond_client_ongoing.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=account_a.units,
            ),
        ).abi_return.accrued_interest
    )

    coupon_amount = fixed_coupon_bond_client_ongoing.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account_a.holding_address),
    ).abi_return.interest
    assert accrued_interest == coupon_amount // 10


def test_on_coupon_due_date() -> None:
    pass  # TODO: Must be tested directly at subroutine level, not through get_payment_amount


def test_fail_pending_coupon_payment() -> None:
    pass  # TODO
