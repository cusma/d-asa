from typing import Callable

import pytest
from algokit_utils import SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    GetAccountInfoArgs,
    PayPrincipalArgs,
)
from tests.utils import (
    Currency,
    DAsaAccount,
    DAsaConfig,
    get_latest_timestamp,
    time_warp,
)


def test_pass_pay_principal(
    currency: Currency,
    account_with_coupons_factory: Callable[..., DAsaAccount],
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    account_all_coupons = account_with_coupons_factory(
        units=fixed_coupon_bond_client_primary.state.global_state.total_units
    )
    # Pre payment state
    pre_payment_state = fixed_coupon_bond_client_primary.state.global_state
    time_warp(pre_payment_state.maturity_date)

    pre_payment_account_info = fixed_coupon_bond_client_primary.send.get_account_info(
        GetAccountInfoArgs(holding_address=account_all_coupons.holding_address),
    ).abi_return

    pre_payment_account_principal = account_all_coupons.principal

    maturity_date = pre_payment_state.maturity_date
    pre_payment_account_units = pre_payment_account_info.units
    pre_payment_circulating_units = pre_payment_state.circulating_units
    assert (
        get_latest_timestamp(fixed_coupon_bond_client_primary.algorand.client.algod)
        >= maturity_date
    )

    # Principal payment
    payment = fixed_coupon_bond_client_primary.send.pay_principal(
        PayPrincipalArgs(
            holding_address=account_all_coupons.holding_address,
            payment_info=b"",
        ),
    ).abi_return

    assert payment.amount == pre_payment_account_principal
    print(
        f"Paid amount: {payment.amount * currency.asa_to_unit:.2f} EUR, Maturity date: {maturity_date}, "
        f"Payment timestamp: {payment.timestamp}"
    )

    # Post payment state
    post_payment_state = fixed_coupon_bond_client_primary.state.global_state

    post_payment_account_info = fixed_coupon_bond_client_primary.send.get_account_info(
        GetAccountInfoArgs(holding_address=account_all_coupons.holding_address),
    ).abi_return

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
    oscar: SigningAccount, fixed_coupon_bond_client_at_maturity: FixedCouponBondClient
) -> None:
    with pytest.raises(Exception, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_at_maturity.send.pay_principal(
            PayPrincipalArgs(
                holding_address=oscar.address,
                payment_info=b"",
            )
        )


def test_fail_no_units(
    account_factory: Callable[..., DAsaAccount],
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    account = account_factory(fixed_coupon_bond_client_primary)

    with pytest.raises(Exception, match=err.NO_UNITS):
        fixed_coupon_bond_client_primary.send.pay_principal(
            PayPrincipalArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )


def test_fail_not_mature(
    account_with_coupons_factory: Callable[..., DAsaAccount],
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    account_all_coupons = account_with_coupons_factory()
    with pytest.raises(Exception, match=err.NOT_MATURE):
        fixed_coupon_bond_client_primary.send.pay_principal(
            PayPrincipalArgs(
                holding_address=account_all_coupons.holding_address,
                payment_info=b"",
            )
        )


def test_fail_pending_coupon_payment(
    fixed_coupon_bond_cfg: DAsaConfig,
    account_with_coupons_factory: Callable[..., DAsaAccount],
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    account = account_with_coupons_factory(
        coupons=fixed_coupon_bond_cfg.total_coupons - 1
    )
    state = fixed_coupon_bond_client_primary.state.global_state
    time_warp(state.maturity_date)
    with pytest.raises(Exception, match=err.PENDING_COUPON_PAYMENT):
        fixed_coupon_bond_client_primary.send.pay_principal(
            PayPrincipalArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )


# TODO: Test the scenario where maturity is reached, an account has a coupon pending but that account is closed
