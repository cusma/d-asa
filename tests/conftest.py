from typing import Final

import pytest
from algokit_utils import (
    EnsureBalanceParameters,
    ensure_funded,
    get_algod_client,
    get_default_localnet_config,
    get_indexer_client,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    AssetCreateParams,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts import constants as sc_cst
from tests import utils

INITIAL_ALGO_FUNDS: Final[int] = 10_000_000_000  # microALGO

DENOMINATION_ASA_NAME: Final[str] = "Euro"
DENOMINATION_ASA_UNIT: Final[str] = "EUR"
DENOMINATION_ASA_DECIMALS: Final[int] = 2
DENOMINATION_ASA_SCALE: Final[int] = 10**DENOMINATION_ASA_DECIMALS
DENOMINATION_ASA_TOTAL: Final[int] = 10_000_000 * DENOMINATION_ASA_SCALE  # 10M Euro

PRINCIPAL: Final[int] = 1_000_000 * DENOMINATION_ASA_SCALE  # 1M Euro
MINIMUM_DENOMINATION: Final[int] = 1_000 * DENOMINATION_ASA_SCALE  # 1k Euro
DAY_COUNT_CONVENTION: Final[list[int]] = [sc_cst.DCC_CONT, sc_cst.DCC_A_A]

PRIMARY_DISTRIBUTION_DELAY: Final[int] = 1 * sc_cst.DAY_2_SEC
PRIMARY_DISTRIBUTION_DURATION: Final[int] = 15 * sc_cst.DAY_2_SEC
ISSUANCE_DELAY: Final[int] = 1 * sc_cst.DAY_2_SEC
MATURITY_DELAY: Final[int] = 1 * sc_cst.DAY_2_SEC

APR: Final[int] = 300  # BPS equal to 3%

TOTAL_UNITS: Final[int] = PRINCIPAL // MINIMUM_DENOMINATION
INITIAL_D_ASA_UNITS: Final[int] = 100


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    # by default we are using localnet algod
    client = get_algod_client(get_default_localnet_config("algod"))
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client(get_default_localnet_config("indexer"))


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client


@pytest.fixture(scope="session")
def arranger(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_ALGO_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def bank(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_ALGO_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def oscar(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_ALGO_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="function")
def currency(algorand_client: AlgorandClient, bank: AddressAndSigner) -> utils.Currency:
    txn_result = algorand_client.send.asset_create(
        AssetCreateParams(
            sender=bank.address,
            signer=bank.signer,
            total=DENOMINATION_ASA_TOTAL,
            decimals=DENOMINATION_ASA_DECIMALS,
            asset_name=DENOMINATION_ASA_NAME,
            unit_name=DENOMINATION_ASA_UNIT,
        )
    )

    return utils.Currency(
        id=txn_result["confirmation"]["asset-index"],
        total=DENOMINATION_ASA_TOTAL,
        decimals=DENOMINATION_ASA_DECIMALS,
        name=DENOMINATION_ASA_NAME,
        unit_name=DENOMINATION_ASA_UNIT,
        asa_to_unit=1 / 10**DENOMINATION_ASA_DECIMALS,
    )


@pytest.fixture(scope="function", params=DAY_COUNT_CONVENTION)
def day_count_convention(request) -> int:  # noqa: ANN001
    return request.param
