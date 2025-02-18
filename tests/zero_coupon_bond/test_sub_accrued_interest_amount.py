from typing import Final

from algokit_utils import AlgorandClient

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    GetAccountUnitsCurrentValueArgs,
    ZeroCouponBondClient,
)
from tests.utils import DAsaAccount, get_latest_timestamp, time_warp

TEST_UNITS: Final[int] = 3


def test_at_issuance(
    algorand: AlgorandClient,
    account_a: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    issuance_date = get_latest_timestamp(
        zero_coupon_bond_client_ongoing.algorand.client.algod
    )
    state = zero_coupon_bond_client_ongoing.state.global_state
    assert issuance_date == state.issuance_date

    value = zero_coupon_bond_client_ongoing.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account_a.holding_address,
            units=account_a.units,
        )
    ).abi_return
    print("Value at issuance:")
    print(value.__dict__)
    assert value.accrued_interest == 0


def test_at_half_period(
    algorand: AlgorandClient,
    account_a: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    issuance_date = get_latest_timestamp(
        zero_coupon_bond_client_ongoing.algorand.client.algod
    )
    state = zero_coupon_bond_client_ongoing.state.global_state
    assert issuance_date == state.issuance_date

    maturity_period = state.maturity_date - issuance_date

    # Principal accrued half period
    half_maturity_period = maturity_period // 2
    time_warp(issuance_date + half_maturity_period)

    value = zero_coupon_bond_client_ongoing.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account_a.holding_address,
            units=account_a.units,
        )
    ).abi_return
    print("Value at half period:")
    print(value.__dict__)
    assert (
        value.accrued_interest
        == (account_a.principal * state.principal_discount // 2) // sc_cst.BPS
    )


def test_on_maturity_date(
    algorand: AlgorandClient,
    account_a: DAsaAccount,
    zero_coupon_bond_client_at_maturity: ZeroCouponBondClient,
) -> None:
    state = zero_coupon_bond_client_at_maturity.state.global_state
    current_date = get_latest_timestamp(
        zero_coupon_bond_client_at_maturity.algorand.client.algod
    )
    assert current_date == state.maturity_date

    value = zero_coupon_bond_client_at_maturity.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account_a.holding_address,
            units=account_a.units,
        )
    ).abi_return
    print("Value at maturity:")
    print(value.__dict__)
    assert value.accrued_interest == 0
