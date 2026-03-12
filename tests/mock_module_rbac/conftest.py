import pytest
from algokit_utils import AlgorandClient, SigningAccount

from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
    MockRbacModuleFactory,
    RbacAssignRoleArgs,
)
from tests import conftest_helpers as helpers
from tests import utils


@pytest.fixture(scope="function")
def rbac_client(
    algorand: AlgorandClient,
    arranger: SigningAccount,
) -> MockRbacModuleClient:
    return helpers.create_bare_client_and_fund(
        algorand,
        MockRbacModuleFactory,
        arranger,
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
