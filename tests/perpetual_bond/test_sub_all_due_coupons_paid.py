from algokit_utils import AlgorandClient, OnCompleteCallParameters

from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from tests.utils import DAsaAccount, DAsaConfig, time_warp

from .conftest import DUE_COUPONS


def test_all_due_coupons_paid(
    algorand: AlgorandClient,
    perpetual_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_ongoing.get_global_state()
    issuance_date = state.issuance_date
    coupon_period = state.coupon_period

    for coupon in range(1, DUE_COUPONS + 1):
        all_paid = (
            perpetual_bond_client_ongoing.get_coupons_status().return_value.all_due_coupons_paid
        )
        assert all_paid

        # Coupon reaches due date
        coupon_due_date = issuance_date + coupon_period * coupon
        time_warp(coupon_due_date)
        all_paid = (
            perpetual_bond_client_ongoing.get_coupons_status().return_value.all_due_coupons_paid
        )
        assert not all_paid

        # Coupon payment
        perpetual_bond_client_ongoing.pay_coupon(
            holding_address=account_a.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                accounts=[account_a.payment_address],
                boxes=[(perpetual_bond_client_ongoing.app_id, account_a.box_id)],
            ),
        )

        all_paid = (
            perpetual_bond_client_ongoing.get_coupons_status().return_value.all_due_coupons_paid
        )
        assert not all_paid

        perpetual_bond_client_ongoing.pay_coupon(
            holding_address=account_b.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                accounts=[account_b.payment_address],
                boxes=[(perpetual_bond_client_ongoing.app_id, account_b.box_id)],
            ),
        )
        all_paid = (
            perpetual_bond_client_ongoing.get_coupons_status().return_value.all_due_coupons_paid
        )
        assert all_paid
