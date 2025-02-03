from typing import Callable, Final

import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    PayCouponArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    CommonAppCallParams,
    PerpetualBondClient,
    UpdateInterestRateArgs,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig, DAsaInterestOracle, time_warp

from .conftest import DUE_COUPONS

D_ASA_TEST_UNITS: Final[int] = 3
INTEREST_RATE_INCREASE: Final[int] = 100  # BPS equal to 1%


def test_pass_primary_distribution(
    algorand: AlgorandClient,
    interest_oracle: DAsaInterestOracle,
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    interest_rate = perpetual_bond_client_primary.state.global_state.interest_rate
    print(f"Interest rate:\t\t{interest_rate / 100:.2f}%")
    perpetual_bond_client_primary.send.update_interest_rate(
        UpdateInterestRateArgs(interest_rate=interest_rate + INTEREST_RATE_INCREASE),
        params=CommonAppCallParams(sender=interest_oracle.address),
    )
    updated_interest_rate = (
        perpetual_bond_client_primary.state.global_state.interest_rate
    )
    print(f"Interest rate:\t\t{updated_interest_rate / 100:.2f}%")
    assert updated_interest_rate == interest_rate + INTEREST_RATE_INCREASE


def test_pass_after_issuance(
    currency: Currency,
    interest_oracle: DAsaInterestOracle,
    perpetual_bond_client_primary: PerpetualBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)
    state = perpetual_bond_client_primary.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    for coupon in range(1, DUE_COUPONS + 1):
        print(f"Interest rate:\t\t{state.interest_rate / 100:.2f}%")
        # Coupon reaches due date
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)

        # Coupon payment
        perpetual_bond_client_primary.send.pay_coupon(
            PayCouponArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )

        # Update interest rate
        interest_rate = state.interest_rate
        perpetual_bond_client_primary.send.update_interest_rate(
            UpdateInterestRateArgs(
                interest_rate=interest_rate + INTEREST_RATE_INCREASE
            ),
            params=CommonAppCallParams(sender=interest_oracle.address),
        )
        state = perpetual_bond_client_primary.state.global_state
        updated_interest_rate = state.interest_rate
        assert updated_interest_rate == interest_rate + INTEREST_RATE_INCREASE


def test_fail_unauthorized(
    algorand: AlgorandClient,
    oscar: SigningAccount,
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    interest_rate = perpetual_bond_client_primary.state.global_state.interest_rate
    with pytest.raises(Exception, match=err.UNAUTHORIZED):
        perpetual_bond_client_primary.send.update_interest_rate(
            UpdateInterestRateArgs(interest_rate=interest_rate + INTEREST_RATE_INCREASE)
        )


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended() -> None:
    pass  # TODO


def test_fail_pending_coupon_payment(
    interest_oracle: DAsaInterestOracle,
    perpetual_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_ongoing.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period
    interest_rate = state.interest_rate

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

        with pytest.raises(Exception, match=err.PENDING_COUPON_PAYMENT):
            perpetual_bond_client_ongoing.send.update_interest_rate(
                UpdateInterestRateArgs(
                    interest_rate=interest_rate + INTEREST_RATE_INCREASE
                ),
                params=CommonAppCallParams(sender=interest_oracle.address),
            )

        perpetual_bond_client_ongoing.send.pay_coupon(
            PayCouponArgs(
                holding_address=second_payee.holding_address,
                payment_info=b"",
            )
        )

        perpetual_bond_client_ongoing.send.update_interest_rate(
            UpdateInterestRateArgs(
                interest_rate=interest_rate + INTEREST_RATE_INCREASE
            ),
            params=CommonAppCallParams(sender=interest_oracle.address),
        )
