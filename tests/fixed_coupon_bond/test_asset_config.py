from copy import deepcopy

import pytest
from algokit_utils import OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
    AssetConfigArgs,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    day_count_convention: int,
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    fixed_coupon_bond_client_empty.send.asset_config(
        AssetConfigArgs(**fixed_coupon_bond_cfg.dictify())
    )

    state = fixed_coupon_bond_client_empty.state.global_state
    expected_coupon_rates = (
        fixed_coupon_bond_client_empty.send.get_coupon_rates().abi_return
    )
    expected_time_events = (
        fixed_coupon_bond_client_empty.send.get_time_events().abi_return
    )

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.settlement_asset_id == state.denomination_asset_id
    assert state.unit_value == fixed_coupon_bond_cfg.minimum_denomination
    assert state.day_count_convention == fixed_coupon_bond_cfg.day_count_convention

    # Principal and Supply
    assert (
        state.total_units
        == fixed_coupon_bond_cfg.principal // fixed_coupon_bond_cfg.minimum_denomination
    )
    assert not state.circulating_units
    assert not state.principal_discount

    # Interest Rate
    assert state.interest_rate == fixed_coupon_bond_cfg.interest_rate

    # Coupons
    assert expected_coupon_rates == fixed_coupon_bond_cfg.coupon_rates
    assert state.total_coupons == fixed_coupon_bond_cfg.total_coupons
    assert not state.paid_coupon_units

    # Time Schedule
    assert expected_time_events == fixed_coupon_bond_cfg.time_events
    assert (
        state.primary_distribution_opening_date
        == fixed_coupon_bond_cfg.time_events[
            sc_cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX
        ]
        # == time_schedule_limits.primary_distribution_opening_date
    )
    assert (
        state.primary_distribution_closure_date
        == fixed_coupon_bond_cfg.time_events[
            sc_cfg.PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX
        ]
        # == time_schedule_limits.primary_distribution_closure_date
    )
    assert (
        state.issuance_date
        == fixed_coupon_bond_cfg.time_events[sc_cfg.ISSUANCE_DATE_IDX]
        # == time_schedule_limits.issuance_date
    )
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date
    assert (
        state.maturity_date
        == fixed_coupon_bond_cfg.time_events[sc_cfg.MATURITY_DATE_IDX]
        # == time_schedule_limits.maturity_date
    )

    # Status
    assert state.status == sc_cfg.STATUS_ACTIVE
    assert not state.suspended


def test_fail_invalid_interest_rate() -> None:
    pass  # TODO


def test_fail_invalid_coupon_rates() -> None:
    pass  # TODO


def test_fail_invalid_time_events_length(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events = [*fixed_coupon_bond_cfg.time_events, 0]
    with pytest.raises(Exception, match=err.INVALID_TIME_EVENTS_LENGTH):
        fixed_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[0] = 0
    with pytest.raises(Exception, match=err.INVALID_TIME):
        fixed_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_sorting(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[-1] = fixed_coupon_bond_cfg.time_events[-2]
    with pytest.raises(Exception, match=err.INVALID_SORTING):
        fixed_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )

    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[0] = fixed_coupon_bond_cfg.time_events[-1]
    with pytest.raises(Exception, match=err.INVALID_SORTING):
        fixed_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention
