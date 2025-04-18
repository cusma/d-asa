from typing import Callable, Final

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    GetAccountUnitsCurrentValueArgs,
    PayCouponArgs,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

D_ASA_TEST_UNITS: Final[int] = 3

# TODO: Add Actual/Actual DDC tests


def test_pass_get_account_units_current_value(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    value = fixed_coupon_bond_client_primary.send.get_account_units_current_value(
        GetAccountUnitsCurrentValueArgs(
            holding_address=account.holding_address,
            units=D_ASA_TEST_UNITS,
        ),
    ).abi_return
    print("Initial units' value:")
    print(value.__dict__)
    assert (
        value.units_value
        == D_ASA_TEST_UNITS * fixed_coupon_bond_cfg.minimum_denomination
    )
    assert not value.accrued_interest

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        next_due_date_idx = sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon
        next_due_date = fixed_coupon_bond_cfg.time_events[next_due_date_idx]
        coupon_period = (
            fixed_coupon_bond_cfg.time_events[next_due_date_idx + 1] - next_due_date
        )
        coupon_period_fraction = 10
        time_warp(next_due_date + coupon_period // coupon_period_fraction)
        if coupon <= fixed_coupon_bond_cfg.total_coupons:
            fixed_coupon_bond_client_primary.send.pay_coupon(
                PayCouponArgs(
                    holding_address=account.holding_address,
                    payment_info=b"",
                )
            )

        units_value = (
            fixed_coupon_bond_client_primary.send.get_account_units_current_value(
                GetAccountUnitsCurrentValueArgs(
                    holding_address=account.holding_address,
                    units=D_ASA_TEST_UNITS,
                ),
            ).abi_return
        )
        print(f"Units' value after {coupon} coupon due date:")
        print(units_value.__dict__)
        assert (
            value.units_value
            == D_ASA_TEST_UNITS * fixed_coupon_bond_cfg.minimum_denomination
        )
        if coupon < fixed_coupon_bond_cfg.total_coupons:
            assert (
                value.accrued_interest
                == value.units_value
                * fixed_coupon_bond_cfg.coupon_rates[coupon]
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
