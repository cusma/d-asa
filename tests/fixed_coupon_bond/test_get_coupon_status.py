from typing import Callable, Final

from algokit_utils import OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp

D_ASA_TEST_UNITS: Final[int] = 3


def test_pass_get_coupon_status(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_with_units_factory(units=D_ASA_TEST_UNITS)

    coupon_status = fixed_coupon_bond_client_primary.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value
    print("Initial coupon status:")
    print(coupon_status.__dict__)
    assert coupon_status.total_coupons == fixed_coupon_bond_cfg.total_coupons
    assert not coupon_status.due_coupons
    assert (
        coupon_status.next_coupon_due_date
        == fixed_coupon_bond_cfg.time_events[sc_cfg.FIRST_COUPON_DATE_IDX]
    )
    assert coupon_status.all_due_coupons_paid
    assert coupon_status.day_count_factor == [0, 0]

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        next_coupon_date_idx = sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon
        next_coupon_due_date = fixed_coupon_bond_cfg.time_events[next_coupon_date_idx]
        coupon_period = (
            fixed_coupon_bond_cfg.time_events[next_coupon_date_idx + 1]
            - next_coupon_due_date
        )
        coupon_period_fraction = 10
        time_warp(next_coupon_due_date + coupon_period // coupon_period_fraction)

        coupon_status = fixed_coupon_bond_client_primary.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            ),
        ).return_value
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
            coupon_status.day_count_factor[0]
            == coupon_status.day_count_factor[1] // coupon_period_fraction
        )

        fixed_coupon_bond_client_primary.pay_coupon(
            holding_address=account.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )
        coupon_status = fixed_coupon_bond_client_primary.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            ),
        ).return_value
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
            coupon_status.day_count_factor[0]
            == coupon_status.day_count_factor[1] // coupon_period_fraction
        )


def test_pass_not_configured(
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    coupon_status = fixed_coupon_bond_client_empty.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value
    print(coupon_status.__dict__)
