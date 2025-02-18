from typing import Callable, Final

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    GetAccountUnitsCurrentValueArgs,
    ZeroCouponBondClient,
)
from tests.utils import DAsaAccount, DAsaConfig, get_latest_timestamp, time_warp

D_ASA_TEST_UNITS: Final[int] = 3


def test_account_units_value_during_primary(
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    state = zero_coupon_bond_client_primary.state.global_state
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    value = zero_coupon_bond_client_primary.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account.holding_address,
            units=D_ASA_TEST_UNITS,
        )
    ).abi_return
    print("Primary distribution units value:")
    print(value.__dict__)
    assert (
        value.units_value
        == account.principal * (sc_cst.BPS - state.principal_discount) // sc_cst.BPS
    )
    assert value.accrued_interest == 0
    assert not value.day_count_factor.numerator
    assert not value.day_count_factor.denominator


def test_account_units_value_at_issuance(
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    state = zero_coupon_bond_client_primary.state.global_state
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    time_warp(state.issuance_date)
    issuance_date = get_latest_timestamp(
        zero_coupon_bond_client_primary.algorand.client.algod
    )
    assert issuance_date == state.issuance_date

    value = zero_coupon_bond_client_primary.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account.holding_address,
            units=D_ASA_TEST_UNITS,
        )
    ).abi_return
    print("Primary distribution units value:")
    print(value.__dict__)

    maturity_period = state.maturity_date - state.issuance_date
    if zero_coupon_bond_cfg.day_count_convention == sc_cst.DCC_A_A:
        maturity_period = maturity_period // sc_cst.DAY_2_SEC

    assert (
        value.units_value
        == account.principal * (sc_cst.BPS - state.principal_discount) // sc_cst.BPS
    )
    assert value.accrued_interest == 0
    assert value.day_count_factor.numerator == 0
    assert value.day_count_factor.denominator == maturity_period


def test_account_units_value_at_maturity(
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    state = zero_coupon_bond_client_primary.state.global_state
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    time_warp(state.maturity_date)
    maturity_date = get_latest_timestamp(
        zero_coupon_bond_client_primary.algorand.client.algod
    )
    assert maturity_date == state.maturity_date

    value = zero_coupon_bond_client_primary.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account.holding_address,
            units=D_ASA_TEST_UNITS,
        )
    ).abi_return
    print("Primary distribution units value:")
    print(value.__dict__)
    assert value.units_value == account.principal
    assert value.accrued_interest == 0
    assert value.day_count_factor.numerator == 0
    assert value.day_count_factor.denominator == 0


def test_fail_no_primary_distribution() -> None:
    pass  # TODO


def test_fail_invalid_holding_address() -> None:
    pass  # TODO


def test_fail_invalid_units() -> None:
    pass  # TODO
