from typing import Callable, Final

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.encoding import decode_address

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig, DAsaInterestOracle, time_warp

from .conftest import DUE_COUPONS

D_ASA_TEST_UNITS: Final[int] = 3
INTEREST_RATE_INCREASE: Final[int] = 100  # BPS equal to 1%


def test_pass_primary_distribution(
    algorand_client: AlgorandClient,
    interest_oracle: DAsaInterestOracle,
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    interest_rate = perpetual_bond_client_primary.get_global_state().interest_rate
    print(f"Interest rate:\t\t{interest_rate / 100:.2f}%")
    perpetual_bond_client_primary.update_interest_rate(
        interest_rate=interest_rate + INTEREST_RATE_INCREASE,
        transaction_parameters=OnCompleteCallParameters(
            signer=interest_oracle.signer,
            boxes=[(perpetual_bond_client_primary.app_id, interest_oracle.box_id)],
        ),
    )
    updated_interest_rate = (
        perpetual_bond_client_primary.get_global_state().interest_rate
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
    state = perpetual_bond_client_primary.get_global_state()
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    for coupon in range(1, DUE_COUPONS + 1):
        print(f"Interest rate:\t\t{state.interest_rate / 100:.2f}%")
        # Coupon reaches due date
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)

        # Coupon payment
        perpetual_bond_client_primary.pay_coupon(
            holding_address=account.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account.payment_address],
                boxes=[(perpetual_bond_client_primary.app_id, account.box_id)],
            ),
        )

        # Update interest rate
        interest_rate = state.interest_rate
        perpetual_bond_client_primary.update_interest_rate(
            interest_rate=interest_rate + INTEREST_RATE_INCREASE,
            transaction_parameters=OnCompleteCallParameters(
                signer=interest_oracle.signer,
                boxes=[(perpetual_bond_client_primary.app_id, interest_oracle.box_id)],
            ),
        )
        state = perpetual_bond_client_primary.get_global_state()
        updated_interest_rate = state.interest_rate
        assert updated_interest_rate == interest_rate + INTEREST_RATE_INCREASE


def test_fail_unauthorized(
    algorand_client: AlgorandClient,
    oscar: AddressAndSigner,
    perpetual_bond_client_primary: PerpetualBondClient,
) -> None:
    interest_rate = perpetual_bond_client_primary.get_global_state().interest_rate
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        perpetual_bond_client_primary.update_interest_rate(
            interest_rate=interest_rate + INTEREST_RATE_INCREASE,
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                boxes=[
                    (
                        perpetual_bond_client_primary.app_id,
                        sc_cst.PREFIX_ID_INTEREST_ORACLE
                        + decode_address(oscar.address),
                    )
                ],
            ),
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
    state = perpetual_bond_client_ongoing.get_global_state()
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

        perpetual_bond_client_ongoing.pay_coupon(
            holding_address=first_payee.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                accounts=[first_payee.payment_address],
                boxes=[(perpetual_bond_client_ongoing.app_id, first_payee.box_id)],
            ),
        )

        with pytest.raises(LogicError, match=err.PENDING_COUPON_PAYMENT):
            perpetual_bond_client_ongoing.update_interest_rate(
                interest_rate=interest_rate + INTEREST_RATE_INCREASE,
                transaction_parameters=OnCompleteCallParameters(
                    signer=interest_oracle.signer,
                    boxes=[
                        (perpetual_bond_client_ongoing.app_id, interest_oracle.box_id)
                    ],
                ),
            )

        perpetual_bond_client_ongoing.pay_coupon(
            holding_address=second_payee.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                accounts=[second_payee.payment_address],
                boxes=[(perpetual_bond_client_ongoing.app_id, second_payee.box_id)],
            ),
        )

        perpetual_bond_client_ongoing.update_interest_rate(
            interest_rate=interest_rate + INTEREST_RATE_INCREASE,
            transaction_parameters=OnCompleteCallParameters(
                signer=interest_oracle.signer,
                boxes=[(perpetual_bond_client_ongoing.app_id, interest_oracle.box_id)],
            ),
        )
