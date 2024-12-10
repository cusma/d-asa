from typing import Callable, Final

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_coupon_amount(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    coupon_rates = fixed_coupon_bond_client_primary.get_coupon_rates(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_COUPON_RATES)
            ]
        ),
    ).return_value

    print(f"Principal: {account.principal * currency.asa_to_unit:.2f} EUR")
    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        coupon_amount = fixed_coupon_bond_client_primary.get_coupon_amount(
            holding_address=account.holding_address,
            coupon=coupon,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ]
            ),
        ).return_value
        coupon_rate_bps = coupon_rates[coupon - 1]
        print(f"Coupon rate {coupon}:\t\t{coupon_rate_bps / 100:.2f}%")
        print(
            f"Coupon amount {coupon}:\t{coupon_amount * currency.asa_to_unit:.2f} EUR\n"
        )
        assert coupon_amount == account.principal * coupon_rate_bps // sc_cst.BPS


def test_pass_not_configured(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(fixed_coupon_bond_client_empty)
    coupon_amount = fixed_coupon_bond_client_empty.get_coupon_amount(
        holding_address=account.holding_address,
        coupon=0,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_empty.app_id, account.box_id),
                (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
            ]
        ),
    ).return_value
    assert coupon_amount == 0


def test_fail_invalid_holding_address(
    oscar: AddressAndSigner, fixed_coupon_bond_client_at_maturity: FixedCouponBondClient
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_at_maturity.get_coupon_amount(
            holding_address=oscar.address,
            coupon=1,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        DAsaAccount.box_id_from_address(oscar.address),
                    ),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ]
            ),
        )


def test_fail_invalid_coupon_index(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    with pytest.raises(LogicError, match=err.INVALID_COUPON_INDEX):
        fixed_coupon_bond_client_primary.get_coupon_amount(
            holding_address=account.holding_address,
            coupon=0,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ]
            ),
        )

    with pytest.raises(LogicError, match=err.INVALID_COUPON_INDEX):
        fixed_coupon_bond_client_primary.get_coupon_amount(
            holding_address=account.holding_address,
            coupon=fixed_coupon_bond_cfg.total_coupons + 1,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ]
            ),
        )
