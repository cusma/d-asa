from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import DAsaConfig, sp_per_coupon, time_warp


def test_count_due_coupons_before_issuance(
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    due_coupons = fixed_coupon_bond_client_primary.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        ),
    ).return_value.due_coupons
    assert due_coupons == 0


def test_count_due_coupons_ongoing(
    algorand_client: AlgorandClient,
    arranger: AddressAndSigner,
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
        time_warp(coupon_due_date)
        due_coupons = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                suggested_params=sp,  # Not needed if the getter is simulated with full opcode budget
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            ),
        ).return_value.due_coupons
        print("Due coupons: ", due_coupons)
        assert due_coupons == coupon


def test_count_due_coupons_at_maturity(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_at_maturity: FixedCouponBondClient,
) -> None:
    due_coupons = fixed_coupon_bond_client_at_maturity.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_at_maturity.app_id, sc_cst.BOX_ID_TIME_EVENTS)
            ],
        ),
    ).return_value.due_coupons
    assert due_coupons == fixed_coupon_bond_cfg.total_coupons
