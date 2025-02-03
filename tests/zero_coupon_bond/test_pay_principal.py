from typing import Callable

import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    GetAccountInfoArgs,
    PayPrincipalArgs,
    ZeroCouponBondClient,
)
from tests.utils import (
    Currency,
    DAsaAccount,
    get_latest_timestamp,
)


def test_pass_pay_principal(
    algorand: AlgorandClient,
    currency: Currency,
    account_a: DAsaAccount,
    zero_coupon_bond_client_at_maturity: ZeroCouponBondClient,
) -> None:
    # Pre payment state
    pre_payment_state = zero_coupon_bond_client_at_maturity.state.global_state

    pre_payment_account_info = (
        zero_coupon_bond_client_at_maturity.send.get_account_info(
            GetAccountInfoArgs(holding_address=account_a.holding_address)
        ).abi_return
    )

    pre_payment_account_principal = account_a.principal

    maturity_date = pre_payment_state.maturity_date
    pre_payment_account_units = pre_payment_account_info.units
    pre_payment_circulating_units = pre_payment_state.circulating_units
    assert (
        get_latest_timestamp(zero_coupon_bond_client_at_maturity.algorand.client.algod)
        >= maturity_date
    )

    # Principal payment
    payment = zero_coupon_bond_client_at_maturity.send.pay_principal(
        PayPrincipalArgs(
            holding_address=account_a.holding_address,
            payment_info=b"",
        )
    ).abi_return

    assert payment.amount == pre_payment_account_principal
    print(
        f"Paid amount: {payment.amount * currency.asa_to_unit:.2f} EUR, Maturity date: {maturity_date}, "
        f"Payment timestamp: {payment.timestamp}"
    )

    # Post payment state
    post_payment_state = zero_coupon_bond_client_at_maturity.state.global_state

    post_payment_account_info = (
        zero_coupon_bond_client_at_maturity.send.get_account_info(
            GetAccountInfoArgs(holding_address=account_a.holding_address)
        ).abi_return
    )

    assert (
        post_payment_state.circulating_units
        == pre_payment_circulating_units - pre_payment_account_units
    )
    assert post_payment_account_info.units == 0
    # TODO: assert balance updates
    # TODO: assert STATUS_ENDED


def test_pass_skip_suspended_account() -> None:
    pass  # TODO


def test_pass_skip_not_opted_in_account() -> None:
    pass  # TODO


def test_fail_unauthorized_status() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended() -> None:
    pass  # TODO


def test_fail_invalid_holding_address(
    oscar: SigningAccount, zero_coupon_bond_client_at_maturity: ZeroCouponBondClient
) -> None:
    with pytest.raises(Exception, match=err.INVALID_HOLDING_ADDRESS):
        zero_coupon_bond_client_at_maturity.send.pay_principal(
            PayPrincipalArgs(
                holding_address=oscar.address,
                payment_info=b"",
            )
        )


def test_fail_no_units(
    account_factory: Callable[..., DAsaAccount],
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
) -> None:
    account = account_factory(zero_coupon_bond_client_primary)

    with pytest.raises(Exception, match=err.NO_UNITS):
        zero_coupon_bond_client_primary.send.pay_principal(
            PayPrincipalArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )


def test_fail_not_mature(
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
    account_a: DAsaAccount,
) -> None:
    with pytest.raises(Exception, match=err.NOT_MATURE):
        zero_coupon_bond_client_primary.send.pay_principal(
            PayPrincipalArgs(
                holding_address=account_a.holding_address,
                payment_info=b"",
            )
        )
