from collections.abc import Callable
from typing import Final

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    GetAccountUnitsCurrentValueArgs,
    PayCouponArgs,
    PerpetualBondClient,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

from .conftest import DUE_COUPONS

D_ASA_TEST_UNITS: Final[int] = 3

# TODO: Add Actual/Actual DDC tests


def test_pass_get_account_units_current_value(
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_primary: PerpetualBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)
    state = perpetual_bond_client_primary.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    value = perpetual_bond_client_primary.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account.holding_address,
            units=D_ASA_TEST_UNITS,
        )
    ).abi_return
    print("Initial units' value:")
    print(value.__dict__)
    assert (
        value.units_value == D_ASA_TEST_UNITS * perpetual_bond_cfg.minimum_denomination
    )
    assert not value.accrued_interest

    for coupon in range(1, DUE_COUPONS + 1):
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)
        coupon_period_fraction = 10
        time_warp(coupon_due_date + coupon_period // coupon_period_fraction)
        if coupon <= DUE_COUPONS:
            perpetual_bond_client_primary.send.pay_coupon(
                PayCouponArgs(
                    holding_address=account.holding_address,
                    payment_info=b"",
                )
            )

        units_value = (
            perpetual_bond_client_primary.send.get_account_units_current_value(
                GetAccountUnitsCurrentValueArgs(
                    holding_address=account.holding_address,
                    units=D_ASA_TEST_UNITS,
                )
            ).abi_return
        )
        print(f"Units' value after {coupon} coupon due date:")
        print(units_value.__dict__)
        assert (
            value.units_value
            == D_ASA_TEST_UNITS * perpetual_bond_cfg.minimum_denomination
        )
        if coupon < perpetual_bond_cfg.total_coupons:
            assert (
                value.accrued_interest
                == value.units_value
                * perpetual_bond_cfg.coupon_rates[coupon]
                * coupon_period_fraction
                // (sc_cst.BPS * coupon_period)
            )
        else:
            assert not value.accrued_interest
        # TODO: validate day count factor


def test_fail_no_primary_distribution() -> None:
    pass  # TODO


def test_fail_invalid_holding_address() -> None:
    pass  # TODO


def test_fail_invalid_units() -> None:
    pass  # TODO


def test_fail_pending_coupon_payment() -> None:
    pass  # TODO
