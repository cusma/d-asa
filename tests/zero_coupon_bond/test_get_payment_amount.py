from typing import Callable, Final

import pytest
from algokit_utils import LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    GetPaymentAmountArgs,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_principal_payment_amount(
    currency: Currency,
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    payment_amount = zero_coupon_bond_client_primary.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account.holding_address)
    ).abi_return

    print(f"Interest rate:\t\t{zero_coupon_bond_cfg.interest_rate / 100:.2f}%")
    print(f"Principal amount:\t{account.principal * currency.asa_to_unit:.2f} EUR")
    print(
        f"Interest amount:\t{payment_amount.interest * currency.asa_to_unit:.2f} EUR\n"
    )
    assert payment_amount.principal == account.principal
    assert (
        payment_amount.interest
        == account.principal * zero_coupon_bond_cfg.interest_rate // sc_cst.BPS
    )


def test_pass_not_configured(
    zero_coupon_bond_client_empty: FixedCouponBondClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(zero_coupon_bond_client_empty)
    payment_amount = zero_coupon_bond_client_empty.send.get_payment_amount(
        GetPaymentAmountArgs(holding_address=account.holding_address)
    ).abi_return
    assert payment_amount.interest == 0
    assert payment_amount.principal == 0


def test_fail_invalid_holding_address(
    oscar: SigningAccount, zero_coupon_bond_client_primary: FixedCouponBondClient
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        zero_coupon_bond_client_primary.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=oscar.address)
        )
