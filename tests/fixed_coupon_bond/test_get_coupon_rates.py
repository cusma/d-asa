from algokit_utils import OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from tests.utils import DAsaConfig


def test_pass_get_coupon_rates(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_active: FixedCouponBondClient,
) -> None:
    coupon_rates = fixed_coupon_bond_client_active.get_coupon_rates(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_active.app_id, sc_cst.BOX_ID_COUPON_RATES)]
        )
    ).return_value
    assert coupon_rates == fixed_coupon_bond_cfg.coupon_rates


def test_pass_not_configured(
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    coupon_rates = fixed_coupon_bond_client_empty.get_coupon_rates(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES)]
        )
    ).return_value
    assert not coupon_rates
