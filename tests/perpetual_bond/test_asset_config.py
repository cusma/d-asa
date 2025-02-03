from copy import deepcopy

import pytest

from smart_contracts import errors as err
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetConfigArgs,
    PerpetualBondClient,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    day_count_convention: int,
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    perpetual_bond_client_empty.send.asset_config(
        AssetConfigArgs(**perpetual_bond_cfg.dictify())
    )

    state = perpetual_bond_client_empty.state.global_state
    expected_time_events = perpetual_bond_client_empty.send.get_time_events().abi_return
    expected_time_periods = (
        perpetual_bond_client_empty.send.get_time_periods().abi_return
    )

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.settlement_asset_id == state.denomination_asset_id
    assert state.unit_value == perpetual_bond_cfg.minimum_denomination
    assert state.day_count_convention == perpetual_bond_cfg.day_count_convention

    # Principal and Supply
    assert (
        state.total_units
        == perpetual_bond_cfg.principal // perpetual_bond_cfg.minimum_denomination
    )
    assert not state.circulating_units
    assert not state.principal_discount

    # Interest Rate
    assert state.interest_rate == perpetual_bond_cfg.interest_rate

    # Coupons
    assert state.total_coupons == perpetual_bond_cfg.total_coupons
    assert state.coupon_period == perpetual_bond_cfg.time_periods[0][0]
    assert not state.paid_coupon_units

    # Time Schedule
    assert expected_time_events == perpetual_bond_cfg.time_events
    # FIXME: algosdk has a bug ARC4 type decoding: https://github.com/algorand/py-algorand-sdk/issues/355
    # assert expected_time_periods == perpetual_bond_cfg.time_periods
    assert not expected_time_periods[0][1]
    assert (
        state.primary_distribution_opening_date
        == perpetual_bond_cfg.time_events[sc_cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX]
        # == time_schedule_limits.primary_distribution_opening_date
    )
    assert (
        state.primary_distribution_closure_date
        == perpetual_bond_cfg.time_events[sc_cfg.PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX]
        # == time_schedule_limits.primary_distribution_closure_date
    )
    assert (
        state.issuance_date
        == perpetual_bond_cfg.time_events[sc_cfg.ISSUANCE_DATE_IDX]
        # == time_schedule_limits.issuance_date
    )
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date
    assert not state.maturity_date

    # Status
    assert state.status == sc_cfg.STATUS_ACTIVE
    assert not state.suspended


def test_fail_invalid_time_events_length(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_events = [*perpetual_bond_cfg.time_events, 0]
    with pytest.raises(Exception, match=err.INVALID_TIME_EVENTS_LENGTH):
        perpetual_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time_periods(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_periods = [*perpetual_bond_cfg.time_periods, (1, 1)]
    with pytest.raises(Exception, match=err.INVALID_TIME_PERIODS):
        perpetual_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time_period_durations(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_periods[0] = (0, 1)
    with pytest.raises(Exception, match=err.INVALID_TIME_PERIOD_DURATION):
        perpetual_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time_period_repetitions(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_periods[0] = (1, 1)
    with pytest.raises(Exception, match=err.INVALID_TIME_PERIOD_REPETITIONS):
        perpetual_bond_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention
