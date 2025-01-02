from copy import deepcopy

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    currency: Currency,
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    base_d_asa_client_empty.asset_config(
        **base_d_asa_cfg.dictify(),
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[base_d_asa_cfg.denomination_asset_id],
            boxes=[
                (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    )

    state = base_d_asa_client_empty.get_global_state()
    expected_coupon_rates = []
    expected_time_events = base_d_asa_client_empty.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.unit_value == base_d_asa_cfg.minimum_denomination
    assert state.day_count_convention == base_d_asa_cfg.day_count_convention

    # Supply
    assert (
        state.total_units
        == base_d_asa_cfg.principal // base_d_asa_cfg.minimum_denomination
    )
    assert not state.circulating_units

    # Interest Rate
    assert state.interest_rate == base_d_asa_cfg.interest_rate

    # Coupons
    assert expected_coupon_rates == base_d_asa_cfg.coupon_rates
    assert state.total_coupons == base_d_asa_cfg.total_coupons

    # Time Schedule
    assert expected_time_events == base_d_asa_cfg.time_events
    assert (
        state.primary_distribution_opening_date
        == base_d_asa_cfg.time_events[sc_cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX]
        # == time_schedule_limits.primary_distribution_opening_date
    )
    assert (
        state.primary_distribution_closure_date
        == base_d_asa_cfg.time_events[sc_cfg.PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX]
        # == time_schedule_limits.primary_distribution_closure_date
    )
    assert (
        state.issuance_date
        == base_d_asa_cfg.time_events[sc_cfg.ISSUANCE_DATE_IDX]
        # == time_schedule_limits.issuance_date
    )
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date
    assert (
        state.maturity_date
        == base_d_asa_cfg.time_events[sc_cfg.MATURITY_DATE_IDX]
        # == time_schedule_limits.maturity_date
    )

    # Status
    assert state.status == sc_cfg.STATUS_ACTIVE
    assert not state.suspended


def test_fail_unauthorized(
    oscar: AddressAndSigner,
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_empty.asset_config(
            **base_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_already_configured(
    base_d_asa_cfg: DAsaConfig, base_d_asa_client_active: BaseDAsaClient
) -> None:
    with pytest.raises(LogicError, match=err.ALREADY_CONFIGURED):
        base_d_asa_client_active.asset_config(
            **base_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_active.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_active.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_minimum_denomination(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.minimum_denomination = wrong_d_asa_cfg.minimum_denomination - 1
    with pytest.raises(LogicError, match=err.INVALID_MINIMUM_DENOMINATION):
        base_d_asa_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_denomination() -> None:
    pass  # TODO


def test_fail_invalid_day_count_convention(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.day_count_convention = 0
    with pytest.raises(LogicError, match=err.INVALID_DAY_COUNT_CONVENTION):
        base_d_asa_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_interest_rate() -> None:
    pass  # TODO


def test_fail_invalid_coupon_rates() -> None:
    pass  # TODO


def test_fail_invalid_time_events_length(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events = [*base_d_asa_cfg.time_events, 0]
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        base_d_asa_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_time(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events[0] = 0
    with pytest.raises(LogicError, match=err.INVALID_TIME):
        base_d_asa_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_sorting(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events[-1] = base_d_asa_cfg.time_events[-2]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        base_d_asa_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )

    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events[0] = base_d_asa_cfg.time_events[-1]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        base_d_asa_client_empty.asset_config(
            **wrong_d_asa_cfg.dictify(),
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[base_d_asa_cfg.denomination_asset_id],
                boxes=[
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                    (base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                ],
            ),
        )


def test_fail_invalid_time_periods() -> None:
    pass  # TODO


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention
