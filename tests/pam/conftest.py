import pytest
from algokit_utils import AlgorandClient

from src.artifacts.dasa_client import (
    DasaClient,
)
from tests import conftest_helpers as helpers
from tests import utils


@pytest.fixture(scope="function")
def pam_primary_dealer(
    algorand: AlgorandClient,
    d_asa_client: DasaClient,
) -> utils.DAsaPrimaryDealer:
    return helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        d_asa_client,
    )


@pytest.fixture(scope="function")
def pam_account_manager(
    algorand: AlgorandClient,
    d_asa_client: DasaClient,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        d_asa_client,
    )
