from typing import Final

from algokit_utils import AlgorandClient, OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from tests.utils import Currency, DAsaAccount, get_latest_timestamp, time_warp

TEST_UNITS: Final[int] = 3

# TODO: Add Actual/Actual DDC tests


def test_from_issuance(
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    current_date = get_latest_timestamp(perpetual_bond_client_ongoing.algod_client)
    next_coupon_due_date = (
        perpetual_bond_client_ongoing.get_coupons_status().return_value.next_coupon_due_date
    )
    state = perpetual_bond_client_ongoing.get_global_state()
    assert current_date == state.issuance_date

    # Coupon accrued half period
    half_coupon_period = (next_coupon_due_date - current_date) // 2
    time_warp(current_date + half_coupon_period)
    due_coupons = (
        perpetual_bond_client_ongoing.get_coupons_status().return_value.due_coupons
    )
    assert due_coupons == 0

    accrued_interest = perpetual_bond_client_ongoing.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_ongoing.app_id, account_a.box_id)]
        ),
    ).return_value.accrued_interest

    coupon_amount = perpetual_bond_client_ongoing.get_payment_amount(
        holding_address=account_a.holding_address,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_ongoing.app_id, account_a.box_id)]
        ),
    ).return_value.interest
    assert accrued_interest == coupon_amount // 2


def test_from_latest_coupon_due_date(
    currency: Currency,
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    first_coupon_due_date = (
        perpetual_bond_client_ongoing.get_coupons_status().return_value.next_coupon_due_date
    )
    time_warp(first_coupon_due_date)
    current_date = get_latest_timestamp(perpetual_bond_client_ongoing.algod_client)
    assert current_date == first_coupon_due_date
    perpetual_bond_client_ongoing.pay_coupon(
        holding_address=account_a.holding_address,
        payment_info=b"",
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[currency.id],
            accounts=[account_a.payment_address],
            boxes=[(perpetual_bond_client_ongoing.app_id, account_a.box_id)],
        ),
    )

    next_coupon_due_date = (
        perpetual_bond_client_ongoing.get_coupons_status().return_value.next_coupon_due_date
    )

    # Coupon accrued a tenth of period
    tenth_coupon_period = (next_coupon_due_date - current_date) // 10
    time_warp(current_date + tenth_coupon_period)
    due_coupons = (
        perpetual_bond_client_ongoing.get_coupons_status().return_value.due_coupons
    )
    assert due_coupons == 1

    accrued_interest = perpetual_bond_client_ongoing.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_ongoing.app_id, account_a.box_id)]
        ),
    ).return_value.accrued_interest

    coupon_amount = perpetual_bond_client_ongoing.get_payment_amount(
        holding_address=account_a.holding_address,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (perpetual_bond_client_ongoing.app_id, account_a.box_id),
                (perpetual_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
            ]
        ),
    ).return_value.interest
    assert accrued_interest == coupon_amount // 10


def test_on_coupon_due_date() -> None:
    pass  # TODO: Must be tested directly at subroutine level, not through get_payment_amount


def test_fail_pending_coupon_payment() -> None:
    pass  # TODO
