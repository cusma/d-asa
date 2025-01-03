from copy import deepcopy

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    fixed_coupon_bond_client_empty.asset_config(
        **fixed_coupon_bond_cfg.dictify(),
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
            boxes=[
                (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    )

    state = fixed_coupon_bond_client_empty.get_global_state()
    expected_coupon_rates = fixed_coupon_bond_client_empty.get_coupon_rates(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES)]
        )
    ).return_value
    expected_time_events = fixed_coupon_bond_client_empty.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.unit_value == fixed_coupon_bond_cfg.minimum_denomination
    assert state.day_count_convention == fixed_coupon_bond_cfg.day_count_convention

    # Supply
    assert (
        state.total_units
        == fixed_coupon_bond_cfg.principal // fixed_coupon_bond_cfg.minimum_denomination
    )
    assert not state.circulating_units

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
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        fixed_coupon_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                boxes=[
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_time(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[0] = 0
    with pytest.raises(LogicError, match=err.INVALID_TIME):
        fixed_coupon_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                boxes=[
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_sorting(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[-1] = fixed_coupon_bond_cfg.time_events[-2]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        fixed_coupon_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                boxes=[
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )

    wrong_d_asa_cfg = deepcopy(fixed_coupon_bond_cfg)
    wrong_d_asa_cfg.time_events[0] = fixed_coupon_bond_cfg.time_events[-1]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        fixed_coupon_bond_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                boxes=[
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (fixed_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention
