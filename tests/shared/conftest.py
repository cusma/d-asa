from collections.abc import Callable
from typing import Any

import pytest
from algokit_utils import AlgorandClient, SigningAccount

from smart_contracts import constants as sc_cst
from tests import conftest_helpers as helpers
from tests import utils
from tests.conftest import INITIAL_D_ASA_UNITS

from .cases import CONTRACT_CASES, ContractCase


@pytest.fixture(scope="function", params=CONTRACT_CASES, ids=lambda case: case.name)
def contract_case(request: pytest.FixtureRequest) -> ContractCase:
    return request.param


@pytest.fixture(scope="function")
def shared_asset_metadata(contract_case: ContractCase) -> Any:
    return contract_case.asset_metadata_cls(
        contract_type=contract_case.metadata_contract_type,
        calendar=sc_cst.CLDR_NC,
        business_day_convention=sc_cst.BDC_NOS,
        end_of_month_convention=sc_cst.EOMC_SD,
        prepayment_effect=sc_cst.PPEF_N,
        penalty_type=sc_cst.PYTP_N,
        prospectus_hash=bytes(32),
        prospectus_url=contract_case.prospectus_url,
    )


@pytest.fixture(scope="function")
def shared_time_events(
    algorand: AlgorandClient,
    contract_case: ContractCase,
) -> utils.TimeEvents:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    return contract_case.build_time_events(current_ts)


@pytest.fixture(scope="function")
def shared_cfg(
    contract_case: ContractCase,
    currency: utils.Currency,
    shared_time_events: utils.TimeEvents,
    day_count_convention: int,
) -> utils.DAsaConfig:
    return contract_case.build_config(
        currency, shared_time_events, day_count_convention
    )


@pytest.fixture(scope="function")
def shared_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    contract_case: ContractCase,
    shared_asset_metadata: Any,
) -> Any:
    return helpers.create_and_fund_client(
        algorand,
        contract_case.factory_class,
        arranger,
        contract_case.asset_create_args_cls(
            arranger=arranger.address,
            metadata=shared_asset_metadata,
        ),
    )


@pytest.fixture(scope="function")
def shared_account_manager(
    algorand: AlgorandClient,
    contract_case: ContractCase,
    shared_client_empty: Any,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        shared_client_empty,
        rbac_assign_role_args_class=contract_case.rbac_assign_role_args_cls,
    )


@pytest.fixture(scope="function")
def shared_authority(
    algorand: AlgorandClient,
    contract_case: ContractCase,
    shared_client_empty: Any,
) -> utils.DAsaAuthority:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        shared_client_empty,
        rbac_assign_role_args_class=contract_case.rbac_assign_role_args_cls,
    )


@pytest.fixture(scope="function")
def shared_trustee(
    algorand: AlgorandClient,
    contract_case: ContractCase,
    shared_client_empty: Any,
) -> utils.DAsaTrustee:
    return helpers.create_role_account(
        algorand,
        utils.DAsaTrustee,
        shared_client_empty,
        rbac_assign_role_args_class=contract_case.rbac_assign_role_args_cls,
    )


@pytest.fixture(scope="function")
def shared_interest_oracle(
    algorand: AlgorandClient,
    contract_case: ContractCase,
    shared_client_empty: Any,
) -> utils.DAsaInterestOracle:
    return helpers.create_role_account(
        algorand,
        utils.DAsaInterestOracle,
        shared_client_empty,
        rbac_assign_role_args_class=contract_case.rbac_assign_role_args_cls,
    )


@pytest.fixture(scope="function")
def shared_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    contract_case: ContractCase,
    shared_cfg: utils.DAsaConfig,
    shared_client_empty: Any,
) -> Any:
    return helpers.activate_client_with_config_and_funding(
        algorand,
        shared_client_empty,
        bank,
        shared_cfg,
        contract_case.total_asa_funds(shared_cfg),
        contract_case.asset_config_args_cls,
    )


@pytest.fixture(scope="function")
def shared_primary_dealer(
    algorand: AlgorandClient,
    contract_case: ContractCase,
    shared_client_active: Any,
) -> utils.DAsaPrimaryDealer:
    state = shared_client_active.state.global_state
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date,
        state.primary_distribution_closure_date,
    )
    return helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        shared_client_active,
        role_config,
        contract_case.rbac_assign_role_args_cls,
    )


@pytest.fixture(scope="function")
def shared_account_factory(
    algorand: AlgorandClient,
    currency: utils.Currency,
    shared_account_manager: utils.DAsaAccountManager,
    contract_case: ContractCase,
) -> Callable[[Any], utils.DAsaAccount]:
    return helpers.build_account_factory(
        algorand,
        currency,
        shared_account_manager,
        contract_case.account_open_args_cls,
    )


@pytest.fixture(scope="function")
def shared_client_primary(
    contract_case: ContractCase,
    shared_client_active: Any,
) -> Any:
    state = shared_client_active.state.global_state
    return helpers.set_client_to_primary_phase(
        shared_client_active,
        contract_case.set_secondary_time_events_args_cls,
        contract_case.secondary_market_time_events(state),
    )


@pytest.fixture(scope="function")
def shared_account_with_units_factory(
    shared_account_factory: Callable[[Any], utils.DAsaAccount],
    shared_primary_dealer: utils.DAsaPrimaryDealer,
    shared_client_primary: Any,
    contract_case: ContractCase,
) -> Callable[..., utils.DAsaAccount]:
    return helpers.build_account_with_units_factory(
        shared_account_factory,
        shared_primary_dealer,
        shared_client_primary,
        contract_case.primary_distribution_args_cls,
        INITIAL_D_ASA_UNITS,
    )


@pytest.fixture(scope="function")
def shared_account_a(
    shared_account_with_units_factory: Callable[..., utils.DAsaAccount],
) -> utils.DAsaAccount:
    return shared_account_with_units_factory()


@pytest.fixture(scope="function")
def shared_account_b(
    shared_account_with_units_factory: Callable[..., utils.DAsaAccount],
) -> utils.DAsaAccount:
    return shared_account_with_units_factory(units=2 * INITIAL_D_ASA_UNITS)


@pytest.fixture(scope="function")
def shared_client_ongoing(shared_client_primary: Any) -> Any:
    state = shared_client_primary.state.global_state
    utils.time_warp(state.issuance_date)
    return shared_client_primary
