from copy import deepcopy

import pytest
from algokit_utils import LogicError

from smart_contracts import errors as err
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetConfigArgs,
    ZeroCouponBondClient,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    day_count_convention: int,
    currency: Currency,
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> None:
    zero_coupon_bond_client_empty.send.asset_config(
        AssetConfigArgs(**zero_coupon_bond_cfg.dictify())
    )

    state = zero_coupon_bond_client_empty.state.global_state
    expected_coupon_rates = []
    expected_time_events = (
        zero_coupon_bond_client_empty.send.get_time_events().abi_return
    )

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.settlement_asset_id == state.denomination_asset_id
    assert state.unit_value == zero_coupon_bond_cfg.minimum_denomination
    assert state.day_count_convention == zero_coupon_bond_cfg.day_count_convention

    # Principal and Supply
    assert (
        state.total_units
        == zero_coupon_bond_cfg.principal // zero_coupon_bond_cfg.minimum_denomination
    )
    assert not state.circulating_units
    assert state.principal_discount == zero_coupon_bond_cfg.principal_discount

    # Interest Rate
    assert state.interest_rate == zero_coupon_bond_cfg.interest_rate

    # Coupons
    assert expected_coupon_rates == zero_coupon_bond_cfg.coupon_rates
    assert state.total_coupons == zero_coupon_bond_cfg.total_coupons

    # Time Schedule
    assert expected_time_events == zero_coupon_bond_cfg.time_events
    assert (
        state.primary_distribution_opening_date
        == zero_coupon_bond_cfg.time_events[
            sc_cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX
        ]
        # == time_schedule_limits.primary_distribution_opening_date
    )
    assert (
        state.primary_distribution_closure_date
        == zero_coupon_bond_cfg.time_events[
            sc_cfg.PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX
        ]
        # == time_schedule_limits.primary_distribution_closure_date
    )
    assert (
        state.issuance_date
        == zero_coupon_bond_cfg.time_events[sc_cfg.ISSUANCE_DATE_IDX]
        # == time_schedule_limits.issuance_date
    )
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date
    assert (
        state.maturity_date
        == zero_coupon_bond_cfg.time_events[sc_cfg.MATURITY_DATE_IDX]
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
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(zero_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events = [*zero_coupon_bond_cfg.time_events, 0]
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        zero_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time(
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(zero_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[0] = 0
    with pytest.raises(LogicError, match=err.INVALID_TIME):
        zero_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_sorting(
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(zero_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[-1] = zero_coupon_bond_cfg.time_events[-2]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        zero_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )

    wrong_d_asa_cfg = deepcopy(zero_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[0] = zero_coupon_bond_cfg.time_events[-1]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        zero_coupon_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention
