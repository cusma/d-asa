import re
from copy import deepcopy
from typing import Any

import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import enums
from smart_contracts import errors as err

from .cases import ContractCase


def test_pass_asset_config(
    contract_case: ContractCase,
    currency: Any,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    shared_client_empty.send.asset_config(
        contract_case.asset_config_args_cls(**shared_cfg.dictify())
    )

    state = shared_client_empty.state.global_state
    expected_time_events = shared_client_empty.send.get_time_events().abi_return

    assert state.denomination_asset_id == currency.id
    assert state.settlement_asset_id == state.denomination_asset_id
    assert state.unit_value == shared_cfg.minimum_denomination
    assert state.day_count_convention == shared_cfg.day_count_convention

    assert state.total_units == shared_cfg.principal // shared_cfg.minimum_denomination
    assert not state.circulating_units
    assert state.principal_discount == shared_cfg.principal_discount
    assert state.interest_rate == shared_cfg.interest_rate
    assert state.total_coupons == shared_cfg.total_coupons

    if contract_case.capabilities.has_coupon_rates:
        expected_coupon_rates = shared_client_empty.send.get_coupon_rates().abi_return
        assert expected_coupon_rates == shared_cfg.coupon_rates

    if contract_case.capabilities.has_time_periods:
        expected_time_periods = shared_client_empty.send.get_time_periods().abi_return
        assert expected_time_periods[0][0] == shared_cfg.time_periods[0][0]
        assert expected_time_periods[0][1] == shared_cfg.time_periods[0][1]
        assert state.coupon_period == shared_cfg.time_periods[0][0]

    assert expected_time_events == shared_cfg.time_events
    assert state.primary_distribution_opening_date == shared_cfg.time_events[0]
    assert state.primary_distribution_closure_date == shared_cfg.time_events[1]
    assert state.issuance_date == shared_cfg.time_events[2]
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date

    if contract_case.capabilities.has_maturity:
        assert state.maturity_date == shared_cfg.time_events[-1]
    else:
        assert not state.maturity_date

    assert state.status == enums.STATUS_ACTIVE
    assert not state.asset_suspended


def test_fail_unauthorized(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**shared_cfg.dictify()),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_already_configured(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_active: Any,
) -> None:
    with pytest.raises(LogicError, match=err.ALREADY_CONFIGURED):
        shared_client_active.send.asset_config(
            contract_case.asset_config_args_cls(**shared_cfg.dictify())
        )


def test_fail_invalid_denomination(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.denomination_asset_id = 0
    with pytest.raises(LogicError, match=err.INVALID_DENOMINATION):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_minimum_denomination(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.minimum_denomination -= 1
    with pytest.raises(LogicError, match=err.INVALID_MINIMUM_DENOMINATION):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_day_count_convention(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.day_count_convention = sc_cst.DCC_CONT - 1
    with pytest.raises(LogicError, match=err.INVALID_DAY_COUNT_CONVENTION):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_interest_rate(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.interest_rate = 1 if shared_cfg.principal_discount else 0
    with pytest.raises(LogicError, match=err.INVALID_INTEREST_RATE):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_coupon_rates(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.coupon_rates = [] if contract_case.capabilities.has_coupon_rates else [1]
    with pytest.raises(LogicError, match=err.INVALID_COUPON_RATES):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_time_events_length(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_events = [*shared_cfg.time_events, 0]
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_time(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_events[0] = 0
    with pytest.raises(LogicError, match=err.INVALID_TIME):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_sorting(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_events[-1] = shared_cfg.time_events[-2]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_time_period_representation(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_periods = (
        [] if contract_case.capabilities.has_time_periods else [(1, 1)]
    )
    with pytest.raises(LogicError, match=err.INVALID_TIME_PERIODS):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_settlement_asset(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.settlement_asset_id = wrong_cfg.denomination_asset_id + 1
    with pytest.raises(LogicError, match=err.INVALID_SETTLEMENT_ASSET):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_time_period_for_actual_actual(
    contract_case: ContractCase,
    day_count_convention: int,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    if day_count_convention != sc_cst.DCC_A_A:
        pytest.skip("requires Actual/Actual day count convention")

    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_events[1] = wrong_cfg.time_events[0] + 1
    with pytest.raises(LogicError, match=re.escape(err.INVALID_TIME_PERIOD)):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_time_period_duration_for_perpetual(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    if not contract_case.capabilities.has_time_periods:
        pytest.skip("contract has no recurring time periods")

    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_periods[0] = (0, 0)
    with pytest.raises(LogicError, match=err.INVALID_TIME_PERIOD_DURATION):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )


def test_fail_invalid_time_period_repetitions_for_perpetual(
    contract_case: ContractCase,
    shared_cfg: Any,
    shared_client_empty: Any,
) -> None:
    if not contract_case.capabilities.has_time_periods:
        pytest.skip("contract has no recurring time periods")

    wrong_cfg = deepcopy(shared_cfg)
    wrong_cfg.time_periods[0] = (shared_cfg.time_periods[0][0], 1)
    with pytest.raises(LogicError, match=err.INVALID_TIME_PERIOD_REPETITIONS):
        shared_client_empty.send.asset_config(
            contract_case.asset_config_args_cls(**wrong_cfg.dictify())
        )
