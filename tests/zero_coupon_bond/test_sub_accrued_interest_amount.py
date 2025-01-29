from typing import Final

from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    ZeroCouponBondClient,
)
from tests.utils import DAsaAccount, get_latest_timestamp, time_warp

TEST_UNITS: Final[int] = 3


def test_at_issuance(
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    issuance_date = get_latest_timestamp(zero_coupon_bond_client_ongoing.algod_client)
    state = zero_coupon_bond_client_ongoing.get_global_state()
    assert issuance_date == state.issuance_date

    value = zero_coupon_bond_client_ongoing.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (zero_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (zero_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (zero_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ]
        ),
    ).return_value
    print("Value at issuance:")
    print(value.__dict__)
    assert value.accrued_interest == 0


def test_at_half_period(
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    issuance_date = get_latest_timestamp(zero_coupon_bond_client_ongoing.algod_client)
    state = zero_coupon_bond_client_ongoing.get_global_state()
    assert issuance_date == state.issuance_date

    maturity_period = state.maturity_date - issuance_date

    # Principal accrued half period
    half_maturity_period = maturity_period // 2
    time_warp(issuance_date + half_maturity_period)

    value = zero_coupon_bond_client_ongoing.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (zero_coupon_bond_client_ongoing.app_id, account_a.box_id),
                (zero_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (zero_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ]
        ),
    ).return_value
    print("Value at half period:")
    print(value.__dict__)
    assert (
        value.accrued_interest
        == (account_a.principal * state.principal_discount // 2) // sc_cst.BPS
    )


def test_on_maturity_date(
    algorand_client: AlgorandClient,
    account_a: DAsaAccount,
    zero_coupon_bond_client_at_maturity: ZeroCouponBondClient,
) -> None:
    state = zero_coupon_bond_client_at_maturity.get_global_state()
    current_date = get_latest_timestamp(
        zero_coupon_bond_client_at_maturity.algod_client
    )
    assert current_date == state.maturity_date

    value = zero_coupon_bond_client_at_maturity.get_account_units_current_value(
        holding_address=account_a.holding_address,
        units=account_a.units,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (zero_coupon_bond_client_at_maturity.app_id, account_a.box_id),
                (
                    zero_coupon_bond_client_at_maturity.app_id,
                    sc_cst.BOX_ID_COUPON_RATES,
                ),
                (zero_coupon_bond_client_at_maturity.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ]
        ),
    ).return_value
    print("Value at maturity:")
    print(value.__dict__)
    assert value.accrued_interest == 0
