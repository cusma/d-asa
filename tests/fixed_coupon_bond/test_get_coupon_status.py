from typing import Callable, Final

from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    PayCouponArgs,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaAccount, DAsaConfig, time_warp

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_coupon_status(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    coupon_status = (
        fixed_coupon_bond_client_primary.send.get_coupons_status().abi_return
    )
    print("Initial coupon status:")
    print(coupon_status.__dict__)
    assert coupon_status.total_coupons == fixed_coupon_bond_cfg.total_coupons
    assert not coupon_status.due_coupons
    assert (
        coupon_status.next_coupon_due_date
        == fixed_coupon_bond_cfg.time_events[sc_cfg.FIRST_COUPON_DATE_IDX]
    )
    assert coupon_status.all_due_coupons_paid
    assert coupon_status.day_count_factor.numerator == 0
    assert coupon_status.day_count_factor.denominator == 0

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        next_coupon_date_idx = sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon
        next_coupon_due_date = fixed_coupon_bond_cfg.time_events[next_coupon_date_idx]
        coupon_period = (
            fixed_coupon_bond_cfg.time_events[next_coupon_date_idx + 1]
            - next_coupon_due_date
        )
        coupon_period_fraction = 10
        time_warp(next_coupon_due_date + coupon_period // coupon_period_fraction)

        coupon_status = (
            fixed_coupon_bond_client_primary.send.get_coupons_status().abi_return
        )
        print(f"Coupon status after {coupon} coupon due date:")
        print(coupon_status.__dict__)
        assert coupon_status.due_coupons == coupon
        if coupon < fixed_coupon_bond_cfg.total_coupons:
            assert (
                coupon_status.next_coupon_due_date
                == fixed_coupon_bond_cfg.time_events[next_coupon_date_idx + 1]
            )
        else:
            assert not coupon_status.next_coupon_due_date
        assert not coupon_status.all_due_coupons_paid
        assert (
            coupon_status.day_count_factor.numerator
            == coupon_status.day_count_factor.denominator // coupon_period_fraction
        )

        fixed_coupon_bond_client_primary.send.pay_coupon(
            PayCouponArgs(holding_address=account.holding_address, payment_info=b""),
        )
        coupon_status = (
            fixed_coupon_bond_client_primary.send.get_coupons_status().abi_return
        )
        print(f"Coupon status after {coupon} coupon payment:")
        print(coupon_status.__dict__)
        assert coupon_status.due_coupons == coupon
        if coupon < fixed_coupon_bond_cfg.total_coupons:
            assert (
                coupon_status.next_coupon_due_date
                == fixed_coupon_bond_cfg.time_events[next_coupon_date_idx + 1]
            )
        else:
            assert not coupon_status.next_coupon_due_date
        assert coupon_status.all_due_coupons_paid
        assert (
            coupon_status.day_count_factor.numerator
            == coupon_status.day_count_factor.denominator // coupon_period_fraction
        )


def test_pass_not_configured(
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    coupon_status = fixed_coupon_bond_client_empty.send.get_coupons_status().abi_return
    print(coupon_status.__dict__)
