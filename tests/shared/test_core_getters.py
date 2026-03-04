from typing import Any

import pytest
from algokit_utils import CommonAppCallParams

from smart_contracts import constants as sc_cst

from .cases import ContractCase


def test_get_time_events_when_not_configured(shared_client_empty: Any) -> None:
    assert not shared_client_empty.send.get_time_events().abi_return


def test_get_time_events_after_config(
    shared_cfg: Any, shared_client_active: Any
) -> None:
    assert (
        shared_client_active.send.get_time_events().abi_return == shared_cfg.time_events
    )


def test_get_asset_metadata(
    shared_asset_metadata: Any, shared_client_empty: Any
) -> None:
    metadata = shared_client_empty.send.get_asset_metadata().abi_return
    assert metadata.contract_type == shared_asset_metadata.contract_type
    assert metadata.prospectus_url == shared_asset_metadata.prospectus_url


def test_get_secondary_market_schedule_default(shared_client_active: Any) -> None:
    schedule = shared_client_active.send.get_secondary_market_schedule().abi_return
    assert schedule == [0, 0]


def test_get_asset_info_active(shared_cfg: Any, shared_client_active: Any) -> None:
    info = shared_client_active.send.get_asset_info().abi_return

    assert info.denomination_asset_id == shared_cfg.denomination_asset_id
    assert info.settlement_asset_id == shared_cfg.settlement_asset_id
    assert info.outstanding_principal == 0
    assert info.unit_value == shared_cfg.minimum_denomination
    assert info.day_count_convention == shared_cfg.day_count_convention
    assert info.principal_discount == shared_cfg.principal_discount
    assert info.interest_rate == shared_cfg.interest_rate
    assert info.total_supply == shared_cfg.principal // shared_cfg.minimum_denomination
    assert info.circulating_supply == 0
    assert info.primary_distribution_opening_date == shared_cfg.time_events[0]
    assert info.primary_distribution_closure_date == shared_cfg.time_events[1]
    assert info.issuance_date == shared_cfg.time_events[2]
    if len(shared_cfg.time_events) > 3:
        assert info.maturity_date == shared_cfg.time_events[-1]
    else:
        assert info.maturity_date == 0
    assert not info.suspended
    assert info.performance == sc_cst.PRF_PERFORMANT


def test_get_asset_info_defaulted(
    contract_case: ContractCase,
    shared_client_ongoing: Any,
    shared_trustee: Any,
) -> None:
    shared_client_ongoing.send.set_default_status(
        contract_case.set_default_status_args_cls(defaulted=True),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    info = shared_client_ongoing.send.get_asset_info().abi_return
    assert info.performance == sc_cst.PRF_DEFAULTED


def test_get_asset_info_matured(
    contract_case: ContractCase,
    shared_client_primary: Any,
) -> None:
    if not contract_case.capabilities.has_maturity:
        pytest.skip("perpetual contract has no maturity date")

    state = shared_client_primary.state.global_state
    from tests.utils import (
        time_warp,
    )  # local import avoids circular fixture module import at load time

    time_warp(state.maturity_date + sc_cst.DAY_2_SEC)
    info = shared_client_primary.send.get_asset_info().abi_return
    assert info.performance == sc_cst.PRF_MATURED
