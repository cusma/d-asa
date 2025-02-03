from typing import Callable, Final

from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PayCouponArgs,
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
    state = perpetual_bond_client_primary.state.global_state
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    coupon_status = perpetual_bond_client_primary.send.get_coupons_status().abi_return
    print("Initial coupon status:")
    print(coupon_status.__dict__)
    assert not coupon_status.total_coupons
    assert not coupon_status.due_coupons
    assert coupon_status.next_coupon_due_date == issuance_date + coupon_period
    assert coupon_status.all_due_coupons_paid
    # FIXME: app client has a bug in decoding nested struct
    # assert coupon_status.day_count_factor.numerator == 0
    # assert coupon_status.day_count_factor.denominator == 0

    for coupon in range(1, DUE_COUPONS + 1):
        coupon_due_date = issuance_date + coupon_period * coupon
        coupon_period_fraction = 10
        time_warp(coupon_due_date + coupon_period // coupon_period_fraction)

        coupon_status = (
            perpetual_bond_client_primary.send.get_coupons_status().abi_return
        )
        print(f"Coupon status after {coupon} coupon due date:")
        print(coupon_status.__dict__)
        assert coupon_status.due_coupons == coupon
        assert coupon_status.next_coupon_due_date == coupon_due_date + coupon_period
        assert not coupon_status.all_due_coupons_paid
        # FIXME: app client has a bug in decoding nested struct
        # assert (
        #     coupon_status.day_count_factor.numerator
        #     == coupon_status.day_count_factor.denominator // coupon_period_fraction
        # )

        perpetual_bond_client_primary.send.pay_coupon(
            PayCouponArgs(
                holding_address=account.holding_address,
                payment_info=b"",
            )
        )
        coupon_status = (
            perpetual_bond_client_primary.send.get_coupons_status().abi_return
        )
        print(f"Coupon status after {coupon} coupon payment:")
        print(coupon_status.__dict__)
        assert coupon_status.due_coupons == coupon
        assert coupon_status.next_coupon_due_date == coupon_due_date + coupon_period
        assert coupon_status.all_due_coupons_paid
        # FIXME: app client has a bug in decoding nested struct
        # assert (
        #     coupon_status.day_count_factor.numerator
        #     == coupon_status.day_count_factor.denominator // coupon_period_fraction
        # )


def test_pass_not_configured(
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    coupon_status = perpetual_bond_client_empty.send.get_coupons_status().abi_return
    print(coupon_status.__dict__)
