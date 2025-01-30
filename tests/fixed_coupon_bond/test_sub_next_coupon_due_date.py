from algokit_utils import AlgorandClient, OnCompleteCallParameters, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaConfig, sp_per_coupon, time_warp

TIME_LEFT_TO_DUE_DATE = 100  # Seconds


def test_next_coupon_due_date_before_issuance(
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_primary.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value
    next_coupon_due_date = fixed_coupon_bond_client_primary.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.next_coupon_due_date
    assert next_coupon_due_date == time_events[sc_cfg.FIRST_COUPON_DATE_IDX]


def test_next_coupon_due_date_ongoing(
    algorand_client: AlgorandClient,
    arranger: SigningAccount,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_ongoing.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value
    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        sp = sp_per_coupon(coupon)
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date - TIME_LEFT_TO_DUE_DATE)
        next_coupon_due_date = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                suggested_params=sp,  # Not needed if the getter is simulated with full opcode budget
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            ),
        ).return_value.next_coupon_due_date
        print("Next coupon due date: ", next_coupon_due_date)
        assert next_coupon_due_date == coupon_due_date


def test_next_coupon_due_date_at_maturity(
    fixed_coupon_bond_client_at_maturity: FixedCouponBondClient,
) -> None:
    next_coupon_due_date = fixed_coupon_bond_client_at_maturity.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_at_maturity.app_id, sc_cst.BOX_ID_TIME_EVENTS)
            ],
        ),
    ).return_value.next_coupon_due_date
    assert next_coupon_due_date == 0
