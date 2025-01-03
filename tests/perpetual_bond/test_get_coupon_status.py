from typing import Callable, Final

from algokit_utils import OnCompleteCallParameters

from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

from .conftest import DUE_COUPONS

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_coupon_status(
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_primary: PerpetualBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)
    state = perpetual_bond_client_primary.get_global_state()
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    coupon_status = perpetual_bond_client_primary.get_coupons_status().return_value
    print("Initial coupon status:")
    print(coupon_status.__dict__)
    assert not coupon_status.total_coupons
    assert not coupon_status.due_coupons
    assert coupon_status.next_coupon_due_date == issuance_date + coupon_period
    assert coupon_status.all_due_coupons_paid
    assert coupon_status.day_count_factor == [0, 0]

    for coupon in range(1, DUE_COUPONS + 1):
        coupon_due_date = issuance_date + coupon_period * coupon
        coupon_period_fraction = 10
        time_warp(coupon_due_date + coupon_period // coupon_period_fraction)

        coupon_status = perpetual_bond_client_primary.get_coupons_status().return_value
        print(f"Coupon status after {coupon} coupon due date:")
        print(coupon_status.__dict__)
        assert coupon_status.due_coupons == coupon
        assert coupon_status.next_coupon_due_date == coupon_due_date + coupon_period
        assert not coupon_status.all_due_coupons_paid
        assert (
            coupon_status.day_count_factor[0]
            == coupon_status.day_count_factor[1] // coupon_period_fraction
        )

        perpetual_bond_client_primary.pay_coupon(
            holding_address=account.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account.payment_address],
                boxes=[(perpetual_bond_client_primary.app_id, account.box_id)],
            ),
        )
        coupon_status = perpetual_bond_client_primary.get_coupons_status().return_value
        print(f"Coupon status after {coupon} coupon payment:")
        print(coupon_status.__dict__)
        assert coupon_status.due_coupons == coupon
        assert coupon_status.next_coupon_due_date == coupon_due_date + coupon_period
        assert coupon_status.all_due_coupons_paid
        assert (
            coupon_status.day_count_factor[0]
            == coupon_status.day_count_factor[1] // coupon_period_fraction
        )


def test_pass_not_configured(
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    coupon_status = perpetual_bond_client_empty.get_coupons_status().return_value
    print(coupon_status.__dict__)
