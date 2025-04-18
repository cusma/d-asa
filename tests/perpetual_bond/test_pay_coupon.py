from typing import Callable

import pytest
from algokit_utils import (
    AlgorandClient,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    GetPaymentAmountArgs,
    PayCouponArgs,
    PerpetualBondClient,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

from .conftest import DUE_COUPONS


def test_pass_pay_coupon(
    algorand: AlgorandClient,
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    account_a_units = account_a.units
    account_b_units = account_b.units
    state = perpetual_bond_client_ongoing.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    for coupon in range(1, DUE_COUPONS + 1):
        print(f"Coupon {coupon}")
        due_coupons = (
            perpetual_bond_client_ongoing.send.get_coupons_status().abi_return.due_coupons
        )
        assert due_coupons == coupon - 1

        # Pre payment sate
        pre_payment_account_a_paid_coupons = account_a.paid_coupons
        pre_payment_account_b_paid_coupons = account_a.paid_coupons
        pre_payment_state = perpetual_bond_client_ongoing.state.global_state
        assert pre_payment_account_a_paid_coupons == due_coupons
        assert pre_payment_account_b_paid_coupons == due_coupons
        assert (
            pre_payment_state.paid_coupon_units
            == account_a_units * pre_payment_account_a_paid_coupons
            + account_b_units * pre_payment_account_b_paid_coupons
        )

        account_a_coupon_amount = perpetual_bond_client_ongoing.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=account_a.holding_address)
        ).abi_return.interest

        account_b_coupon_amount = perpetual_bond_client_ongoing.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=account_b.holding_address)
        ).abi_return.interest

        # Coupon reaches due date
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)
        due_coupons = (
            perpetual_bond_client_ongoing.send.get_coupons_status().abi_return.due_coupons
        )
        assert due_coupons == coupon

        # Coupon payment
        payment_a = perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=account_a.holding_address,
                payment_info=b"",
            )
        ).abi_return
        assert payment_a.amount == account_a_coupon_amount
        print("Account A:")
        print(
            f"Paid amount: {payment_a.amount * currency.asa_to_unit:.2f} EUR, Due date: {coupon_due_date}, "
            f"Payment timestamp: {payment_a.timestamp}"
        )

        payment_b = perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=account_b.holding_address,
                payment_info=b"",
            )
        ).abi_return
        assert payment_b.amount == account_b_coupon_amount
        print("Account B:")
        print(
            f"Paid amount: {payment_b.amount * currency.asa_to_unit:.2f} EUR, Due date: {coupon_due_date}, "
            f"Payment timestamp: {payment_b.timestamp}\n"
        )

        # Post payment state
        post_payment_account_a_paid_coupons = account_a.paid_coupons
        post_payment_account_b_paid_coupons = account_b.paid_coupons
        post_payment_state = perpetual_bond_client_ongoing.state.global_state
        assert (
            post_payment_account_a_paid_coupons
            == pre_payment_account_a_paid_coupons + 1
        )
        assert (
            post_payment_account_b_paid_coupons
            == pre_payment_account_b_paid_coupons + 1
        )
        assert (
            post_payment_state.paid_coupon_units
            == account_a_units * post_payment_account_a_paid_coupons
            + account_b_units * post_payment_account_b_paid_coupons
        )
        # TODO: assert balance updates


def test_pass_pay_multiple_coupons(
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    account_units = account_a.units
    state = perpetual_bond_client_ongoing.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    time_warp(issuance_date + coupon_period * DUE_COUPONS)

    due_coupons = (
        perpetual_bond_client_ongoing.send.get_coupons_status().abi_return.due_coupons
    )
    assert due_coupons == DUE_COUPONS

    for coupon in range(1, DUE_COUPONS + 1):
        print(f"Coupon {coupon}")
        coupon_amount = perpetual_bond_client_ongoing.send.get_payment_amount(
            GetPaymentAmountArgs(holding_address=account_a.holding_address)
        ).abi_return.interest

        # Pre payment sate
        pre_payment_account_paid_coupons = account_a.paid_coupons
        pre_payment_state = perpetual_bond_client_ongoing.state.global_state
        assert (
            pre_payment_state.paid_coupon_units
            == account_units * pre_payment_account_paid_coupons
        )

        # Coupon payment
        coupon_due_date = pre_payment_state.issuance_date + state.coupon_period * coupon
        payment = perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=account_a.holding_address,
                payment_info=b"",
            )
        ).abi_return
        assert payment.amount == coupon_amount
        print(
            f"Paid amount: {payment.amount * currency.asa_to_unit:.2f} EUR, Due date: {coupon_due_date}, "
            f"Payment timestamp: {payment.timestamp}"
        )

        # Post payment state
        post_payment_account_paid_coupons = account_a.paid_coupons
        post_payment_state = perpetual_bond_client_ongoing.state.global_state
        assert post_payment_account_paid_coupons == pre_payment_account_paid_coupons + 1
        assert (
            post_payment_state.paid_coupon_units
            == account_units * post_payment_account_paid_coupons
        )
        # TODO: assert balance updates


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
    oscar: SigningAccount, perpetual_bond_client_ongoing: PerpetualBondClient
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=oscar.address,
                payment_info=b"",
            )
        )


def test_fail_no_units(
    account_factory: Callable[..., DAsaAccount],
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    account = account_factory(perpetual_bond_client_primary)

    with pytest.raises(LogicError, match=err.NO_UNITS):
        perpetual_bond_client_primary.send.pay_coupon(
            PayCouponArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )


def test_fail_no_due_coupon(
    algorand: AlgorandClient,
    perpetual_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_ongoing.state.global_state

    for coupon in range(1, DUE_COUPONS + 1):
        with pytest.raises(LogicError, match=err.NO_DUE_COUPON):
            perpetual_bond_client_ongoing.send.pay_coupon(
                PayCouponArgs(
                    holding_address=account_a.holding_address,
                    payment_info=b"",
                )
            )
        coupon_due_date = state.issuance_date + state.coupon_period * coupon
        time_warp(coupon_due_date)
        perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=account_a.holding_address,
                payment_info=b"",
            )
        )


def test_fail_pending_coupon_payment(
    perpetual_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_ongoing.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    for coupon in range(1, DUE_COUPONS):
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)
        if coupon % 2:
            first_payee = account_a
            second_payee = account_b
        else:
            first_payee = account_b
            second_payee = account_a

        perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=first_payee.holding_address,
                payment_info=b"",
            )
        )

        coupon_due_date = issuance_date + coupon_period * (coupon + 1)
        time_warp(coupon_due_date)
        with pytest.raises(LogicError, match=err.PENDING_COUPON_PAYMENT):
            perpetual_bond_client_ongoing.send.pay_coupon(
                PayCouponArgs(
                    holding_address=first_payee.holding_address,
                    payment_info=b"",
                )
            )

        perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=second_payee.holding_address,
                payment_info=b"",
            )
        )
