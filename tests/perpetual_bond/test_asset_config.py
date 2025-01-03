from copy import deepcopy

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondClient,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    currency: Currency,
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    perpetual_bond_client_empty.asset_config(
        **perpetual_bond_cfg.dictify(),
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
            boxes=[
                (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS),
            ],
        ),
    )

    state = perpetual_bond_client_empty.get_global_state()
    expected_time_events = perpetual_bond_client_empty.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value
    expected_time_periods = perpetual_bond_client_empty.get_time_periods(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS)]
        )
    ).return_value

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.unit_value == perpetual_bond_cfg.minimum_denomination
    assert state.day_count_convention == perpetual_bond_cfg.day_count_convention

    # Supply
    assert (
        state.total_units
        == perpetual_bond_cfg.principal // perpetual_bond_cfg.minimum_denomination
    )
    assert not state.circulating_units

    # Interest Rate
    assert state.interest_rate == perpetual_bond_cfg.interest_rate

    # Coupons
    assert state.total_coupons == perpetual_bond_cfg.total_coupons
    assert state.coupon_period == perpetual_bond_cfg.time_periods[0][0]
    assert not state.paid_coupon_units

    # Time Schedule
    assert expected_time_events == perpetual_bond_cfg.time_events
    # FIXME: assert expected_time_periods == perpetual_bond_cfg.time_periods, algosdk has a bug ARC4 type decoding
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
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        perpetual_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                boxes=[
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS),
                ],
            ),
        )


def test_fail_invalid_time_periods(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_periods = [*perpetual_bond_cfg.time_periods, (1, 1)]
    with pytest.raises(LogicError, match=err.INVALID_TIME_PERIODS):
        perpetual_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                boxes=[
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS),
                ],
            ),
        )


def test_fail_invalid_time_period_durations(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_periods[0] = (0, 1)
    with pytest.raises(LogicError, match=err.INVALID_TIME_PERIOD_DURATION):
        perpetual_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                boxes=[
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS),
                ],
            ),
        )


def test_fail_invalid_time_period_repetitions(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(perpetual_bond_cfg)
    wrong_d_asa_cfg.time_periods[0] = (1, 1)
    with pytest.raises(LogicError, match=err.INVALID_TIME_PERIOD_REPETITIONS):
        perpetual_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
                boxes=[
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                    (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS),
                ],
            ),
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention