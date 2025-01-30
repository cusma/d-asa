from algokit_utils import AlgorandClient, OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaAccount, DAsaConfig, time_warp


def test_all_due_coupons_paid(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_ongoing.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        all_paid = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            )
        ).return_value.all_due_coupons_paid
        assert all_paid

        # Coupon reaches due date
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date)
        all_paid = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            )
        ).return_value.all_due_coupons_paid
        assert not all_paid

        # Coupon payment
        fixed_coupon_bond_client_ongoing.pay_coupon(
            holding_address=account_a.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                accounts=[account_a.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )

        all_paid = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            )
        ).return_value.all_due_coupons_paid
        assert not all_paid

        fixed_coupon_bond_client_ongoing.pay_coupon(
            holding_address=account_b.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                accounts=[account_b.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )
        all_paid = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            )
        ).return_value.all_due_coupons_paid
        assert all_paid
