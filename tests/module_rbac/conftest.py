import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
    MockRbacModuleFactory,
    RbacAssignRoleArgs,
)
from tests import conftest_helpers as helpers
from tests import utils
from tests.shared import conftest as shared_fixtures

contract_case = shared_fixtures.contract_case
shared_asset_metadata = shared_fixtures.shared_asset_metadata
shared_time_events = shared_fixtures.shared_time_events
shared_cfg = shared_fixtures.shared_cfg
shared_client_empty = shared_fixtures.shared_client_empty
shared_account_manager = shared_fixtures.shared_account_manager
shared_authority = shared_fixtures.shared_authority
shared_trustee = shared_fixtures.shared_trustee
shared_interest_oracle = shared_fixtures.shared_interest_oracle
shared_client_active = shared_fixtures.shared_client_active
shared_primary_dealer = shared_fixtures.shared_primary_dealer
shared_account_factory = shared_fixtures.shared_account_factory
shared_client_primary = shared_fixtures.shared_client_primary
shared_account_with_units_factory = shared_fixtures.shared_account_with_units_factory
shared_account_a = shared_fixtures.shared_account_a
shared_account_b = shared_fixtures.shared_account_b
shared_client_ongoing = shared_fixtures.shared_client_ongoing


@pytest.fixture(scope="function")
def rbac_client(
    algorand: AlgorandClient,
    arranger: SigningAccount,
) -> MockRbacModuleClient:
    return helpers.create_bare_client_and_fund(
        algorand, MockRbacModuleFactory, arranger
    )


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    rbac_client: MockRbacModuleClient,
) -> utils.DAsaAuthority:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        rbac_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def trustee(
    algorand: AlgorandClient,
    rbac_client: MockRbacModuleClient,
) -> utils.DAsaTrustee:
    return helpers.create_role_account(
        algorand,
        utils.DAsaTrustee,
        rbac_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    rbac_client: MockRbacModuleClient,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        rbac_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient,
    rbac_client: MockRbacModuleClient,
) -> utils.DAsaPrimaryDealer:
    return helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        rbac_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def interest_oracle(
    algorand: AlgorandClient,
    rbac_client: MockRbacModuleClient,
) -> utils.DAsaInterestOracle:
    return helpers.create_role_account(
        algorand,
        utils.DAsaInterestOracle,
        rbac_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )
