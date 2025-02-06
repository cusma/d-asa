from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from tests.utils import DAsaConfig


def test_pass_get_coupon_rates(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_active: FixedCouponBondClient,
) -> None:
    coupon_rates = fixed_coupon_bond_client_active.send.get_coupon_rates().abi_return
    assert coupon_rates == fixed_coupon_bond_cfg.coupon_rates


def test_pass_not_configured(
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    coupon_rates = fixed_coupon_bond_client_empty.send.get_coupon_rates().abi_return
    assert not coupon_rates
