from collections.abc import Callable
from typing import Final

import pytest
from algokit_utils import LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    GetPaymentAmountArgs,
    PayCouponArgs,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_coupon_payment_amount(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    time_events = fixed_coupon_bond_client_primary.send.get_time_events().abi_return

    coupon_rates = fixed_coupon_bond_client_primary.send.get_coupon_rates().abi_return

    print(f"Principal: {account.principal * currency.asa_to_unit:.2f} EUR")
    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        payment_amount = fixed_coupon_bond_client_primary.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=account.holding_address),
        ).abi_return
        coupon_rate_bps = coupon_rates[coupon - 1]
        print(f"Coupon rate {coupon}:\t\t{coupon_rate_bps / 100:.2f}%")
        print(
            f"Coupon amount {coupon}:\t{payment_amount.interest * currency.asa_to_unit:.2f} EUR\n"
        )
        assert (
            payment_amount.interest == account.principal * coupon_rate_bps // sc_cst.BPS
        )
        assert payment_amount.principal == 0

        # Coupon reaches due date
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date)
        fixed_coupon_bond_client_primary.send.pay_coupon(
            PayCouponArgs(holding_address=account.holding_address, payment_info=b"")
        )


def test_pass_get_principal_payment_amount(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_coupons_factory: Callable[..., DAsaAccount],
) -> None:
    # Account with all coupons paid and principal repayment left
    account = account_with_coupons_factory()

    payment_amount = fixed_coupon_bond_client_primary.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account.holding_address),
    ).abi_return

    print(f"Interest rate:\t\t{fixed_coupon_bond_cfg.interest_rate / 100:.2f}%")
    print(f"Principal amount:\t{account.principal * currency.asa_to_unit:.2f} EUR")
    print(f"Interest amount with principal:\t{0:.2f} EUR\n")
    assert payment_amount.principal == account.principal
    assert payment_amount.interest == 0


def test_pass_not_configured(
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(fixed_coupon_bond_client_empty)
    payment_amount = fixed_coupon_bond_client_empty.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account.holding_address),
    ).abi_return
    assert payment_amount.interest == 0
    assert payment_amount.principal == 0


def test_fail_invalid_holding_address(
    oscar: SigningAccount, fixed_coupon_bond_client_at_maturity: FixedCouponBondClient
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_at_maturity.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=oscar.address),
        )
