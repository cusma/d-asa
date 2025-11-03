from collections.abc import Callable
from typing import Final

import pytest
from algokit_utils import LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    PayCouponArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    GetPaymentAmountArgs,
    PerpetualBondClient,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

from .conftest import DUE_COUPONS

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_coupon_payment_amount(
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_primary: PerpetualBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)
    state = perpetual_bond_client_primary.state.global_state

    print(f"Principal: {account.principal * currency.asa_to_unit:.2f} EUR")
    for coupon in range(1, DUE_COUPONS + 1):
        payment_amount = perpetual_bond_client_primary.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=account.holding_address)
        ).abi_return
        coupon_rate_bps = perpetual_bond_cfg.interest_rate
        print(f"Coupon rate {coupon}:\t\t{coupon_rate_bps / 100:.2f}%")
        print(
            f"Coupon amount {coupon}:\t{payment_amount.interest * currency.asa_to_unit:.2f} EUR\n"
        )
        assert (
            payment_amount.interest == account.principal * coupon_rate_bps // sc_cst.BPS
        )
        assert payment_amount.principal == 0

        # Coupon reaches due date
        coupon_due_date = state.issuance_date + state.coupon_period * coupon
        time_warp(coupon_due_date)
        perpetual_bond_client_primary.send.pay_coupon(
            PayCouponArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )


def test_pass_not_configured(
    perpetual_bond_client_empty: PerpetualBondClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(perpetual_bond_client_empty)
    payment_amount = perpetual_bond_client_empty.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account.holding_address)
    ).abi_return
    assert payment_amount.interest == 0
    assert payment_amount.principal == 0


def test_fail_invalid_holding_address(
    oscar: SigningAccount, perpetual_bond_client_ongoing: PerpetualBondClient
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        perpetual_bond_client_ongoing.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=oscar.address)
        )
