from copy import deepcopy

import pytest
from algokit_utils import CommonAppCallParams, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetConfigArgs,
    BaseDAsaClient,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import Currency, DAsaConfig


def test_pass_asset_config(
    day_count_convention: int,
    currency: Currency,
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    base_d_asa_client_empty.send.asset_config(
        AssetConfigArgs(**base_d_asa_cfg.dictify())
    )

    state = base_d_asa_client_empty.state.global_state
    expected_coupon_rates = []
    expected_time_events = base_d_asa_client_empty.send.get_time_events().abi_return

    # Asset Configuration
    assert state.denomination_asset_id == currency.id
    assert state.settlement_asset_id == state.denomination_asset_id
    assert state.unit_value == base_d_asa_cfg.minimum_denomination
    assert state.day_count_convention == base_d_asa_cfg.day_count_convention

    # Principal and Supply
    assert (
        state.total_units
        == base_d_asa_cfg.principal // base_d_asa_cfg.minimum_denomination
    )
    assert not state.circulating_units
    assert not state.principal_discount

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
    oscar: SigningAccount,
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    with pytest.raises(Exception, match=err.UNAUTHORIZED):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**base_d_asa_cfg.dictify()),
            params=CommonAppCallParams(sender=oscar.address),
        )


def test_fail_already_configured(
    base_d_asa_cfg: DAsaConfig, base_d_asa_client_active: BaseDAsaClient
) -> None:
    with pytest.raises(Exception, match=err.ALREADY_CONFIGURED):
        base_d_asa_client_active.send.asset_config(
            AssetConfigArgs(**base_d_asa_cfg.dictify())
        )


def test_fail_invalid_minimum_denomination(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.minimum_denomination = wrong_d_asa_cfg.minimum_denomination - 1
    with pytest.raises(Exception, match=err.INVALID_MINIMUM_DENOMINATION):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_denomination() -> None:
    pass  # TODO


def test_fail_invalid_day_count_convention(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.day_count_convention = sc_cst.DCC_CONT - 1
    with pytest.raises(Exception, match=err.INVALID_DAY_COUNT_CONVENTION):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
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
    with pytest.raises(Exception, match=err.INVALID_TIME_EVENTS_LENGTH):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events[0] = 0
    with pytest.raises(Exception, match=err.INVALID_TIME):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_sorting(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events[-1] = base_d_asa_cfg.time_events[-2]
    with pytest.raises(Exception, match=err.INVALID_SORTING):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )

    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.time_events[0] = base_d_asa_cfg.time_events[-1]
    with pytest.raises(Exception, match=err.INVALID_SORTING):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


def test_fail_invalid_time_periods() -> None:
    pass  # TODO


def test_fail_invalid_settlement_asset(
    base_d_asa_cfg: DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    wrong_d_asa_cfg = deepcopy(base_d_asa_cfg)
    wrong_d_asa_cfg.settlement_asset_id = wrong_d_asa_cfg.denomination_asset_id + 1
    with pytest.raises(Exception, match=err.INVALID_SETTLEMENT_ASSET):
        base_d_asa_client_empty.send.asset_config(
            AssetConfigArgs(**wrong_d_asa_cfg.dictify())
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention
