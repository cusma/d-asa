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
from tests import utils
from tests.conftest import INITIAL_ALGO_FUNDS


@pytest.fixture(scope="function")
def rbac_client(
    algorand: AlgorandClient,
    arranger: SigningAccount,
) -> MockRbacModuleClient:
    factory = algorand.client.get_typed_app_factory(
        MockRbacModuleFactory,
        default_sender=arranger.address,
        default_signer=arranger.signer,
    )
    client, _ = factory.send.create.bare()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return client


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    rbac_client: MockRbacModuleClient,
) -> utils.DAsaAuthority:
    account = algorand.account.random()
    account = utils.DAsaAuthority(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    rbac_client.send.rbac_assign_role(
        RbacAssignRoleArgs(
            role_id=account.role_id(),
            role_address=account.address,
            config=role_config,
        )
    )
    return account
