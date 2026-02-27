import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    MockAccountingModuleClient,
    MockAccountingModuleFactory,
    RbacAssignRoleArgs,
)
from tests import conftest_helpers as helpers
from tests import utils


@pytest.fixture(scope="function")
def accounting_client(
    algorand: AlgorandClient,
    arranger: SigningAccount,
) -> MockAccountingModuleClient:
    return helpers.create_bare_client_and_fund(
        algorand, MockAccountingModuleFactory, arranger
    )


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    accounting_client: MockAccountingModuleClient,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        accounting_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    accounting_client: MockAccountingModuleClient,
) -> utils.DAsaAuthority:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        accounting_client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )
