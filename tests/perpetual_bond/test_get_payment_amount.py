from typing import Callable, Final

import pytest
from algokit_utils import OnCompleteCallParameters, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
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
    state = perpetual_bond_client_primary.get_global_state()

    print(f"Principal: {account.principal * currency.asa_to_unit:.2f} EUR")
    for coupon in range(1, DUE_COUPONS + 1):
        payment_amount = perpetual_bond_client_primary.get_payment_amount(
            holding_address=account.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(perpetual_bond_client_primary.app_id, account.box_id)]
            ),
        ).return_value
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
        perpetual_bond_client_primary.pay_coupon(
            holding_address=account.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account.payment_address],
                boxes=[(perpetual_bond_client_primary.app_id, account.box_id)],
            ),
        )


def test_pass_not_configured(
    perpetual_bond_client_empty: PerpetualBondClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(perpetual_bond_client_empty)
    payment_amount = perpetual_bond_client_empty.get_payment_amount(
        holding_address=account.holding_address,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, account.box_id)]
        ),
    ).return_value
    assert payment_amount.interest == 0
    assert payment_amount.principal == 0


def test_fail_invalid_holding_address(
    oscar: SigningAccount, perpetual_bond_client_ongoing: PerpetualBondClient
) -> None:
    with pytest.raises(Exception, match=err.INVALID_HOLDING_ADDRESS):
        perpetual_bond_client_ongoing.get_payment_amount(
            holding_address=oscar.address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (
                        perpetual_bond_client_ongoing.app_id,
                        DAsaAccount.box_id_from_address(oscar.address),
                    )
                ]
            ),
        )
