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
