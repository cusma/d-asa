import pytest
from algokit_utils import AlgorandClient, SigningAccount

from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
    MockRbacModuleFactory,
)
from tests import conftest_helpers as helpers
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
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        rbac_client,
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
    )
