from typing import Final

from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from tests.utils import Currency, DAsaAccount, get_latest_timestamp, time_warp

TEST_UNITS: Final[int] = 3

# TODO: Add Actual/Actual DDC tests


def test_from_issuance(
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    current_date = get_latest_timestamp(fixed_coupon_bond_client_ongoing.algod_client)
    next_coupon_due_date = fixed_coupon_bond_client_ongoing.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.next_coupon_due_date
    state = fixed_coupon_bond_client_ongoing.get_global_state()
    assert current_date == state.issuance_date

    # Coupon accrued half period
    half_coupon_period = (next_coupon_due_date - current_date) // 2
    time_warp(current_date + half_coupon_period)
    due_coupons = fixed_coupon_bond_client_ongoing.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.due_coupons
    assert due_coupons == 0

    accrued_interest = fixed_coupon_bond_client_ongoing.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ]
        ),
    ).return_value.accrued_interest

    coupon_amount = fixed_coupon_bond_client_ongoing.get_payment_amount(
        holding_address=account_a.holding_address,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
            ]
        ),
    ).return_value.interest
    assert accrued_interest == coupon_amount // 2


def test_from_latest_coupon_due_date(
    currency: Currency,
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    first_coupon_due_date = fixed_coupon_bond_client_ongoing.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.next_coupon_due_date
    time_warp(first_coupon_due_date)
    current_date = get_latest_timestamp(fixed_coupon_bond_client_ongoing.algod_client)
    assert current_date == first_coupon_due_date
    fixed_coupon_bond_client_ongoing.pay_coupon(
        holding_address=account_a.holding_address,
        payment_info=b"",
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[currency.id],
            accounts=[account_a.payment_address],
            boxes=[
                (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (
                    fixed_coupon_bond_client_ongoing.app_id,
                    sc_cst.BOX_ID_COUPON_RATES,
                ),
                (
                    fixed_coupon_bond_client_ongoing.app_id,
                    sc_cst.BOX_ID_TIME_EVENTS,
                ),
            ],
        ),
    )

    next_coupon_due_date = fixed_coupon_bond_client_ongoing.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.next_coupon_due_date

    # Coupon accrued a tenth of period
    tenth_coupon_period = (next_coupon_due_date - current_date) // 10
    time_warp(current_date + tenth_coupon_period)
    due_coupons = fixed_coupon_bond_client_ongoing.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.due_coupons
    assert due_coupons == 1

    accrued_interest = fixed_coupon_bond_client_ongoing.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ]
        ),
    ).return_value.accrued_interest

    coupon_amount = fixed_coupon_bond_client_ongoing.get_payment_amount(
        holding_address=account_a.holding_address,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
            ]
        ),
    ).return_value.interest
    assert accrued_interest == coupon_amount // 10


def test_on_coupon_due_date() -> None:
    pass  # TODO: Must be tested directly at subroutine level, not through get_payment_amount


def test_fail_pending_coupon_payment() -> None:
    pass  # TODO
