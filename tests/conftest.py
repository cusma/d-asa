from typing import Final

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AssetCreateParams,
    SigningAccount,
)
from algokit_utils.config import config

from tests import utils

INITIAL_ALGO_FUNDS: Final[AlgoAmount] = AlgoAmount.from_algo(10_000)

DENOMINATION_ASA_NAME: Final[str] = "Euro"
DENOMINATION_ASA_UNIT: Final[str] = "€"
DENOMINATION_ASA_DECIMALS: Final[int] = 2
DENOMINATION_ASA_SCALE: Final[int] = 10**DENOMINATION_ASA_DECIMALS
DENOMINATION_ASA_TOTAL: Final[int] = 10_000_000 * DENOMINATION_ASA_SCALE  # 10M Euro


@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    config.configure(
        debug=True,
        populate_app_call_resources=True,
    )

    client = AlgorandClient.default_localnet()
    client.set_suggested_params_cache_timeout(0)
    return client


@pytest.fixture(scope="session")
def arranger(algorand: AlgorandClient) -> SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def bank(algorand: AlgorandClient) -> SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def no_role_account(algorand: AlgorandClient) -> SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return account


@pytest.fixture(scope="function")
def currency(algorand: AlgorandClient, bank: SigningAccount) -> utils.Currency:
    currency_id = algorand.send.asset_create(
        AssetCreateParams(
            sender=bank.address,
            signer=bank.signer,
            total=DENOMINATION_ASA_TOTAL,
            decimals=DENOMINATION_ASA_DECIMALS,
            asset_name=DENOMINATION_ASA_NAME,
            unit_name=DENOMINATION_ASA_UNIT,
        )
    ).asset_id

    return utils.Currency(
        id=currency_id,
        total=DENOMINATION_ASA_TOTAL,
        decimals=DENOMINATION_ASA_DECIMALS,
        name=DENOMINATION_ASA_NAME,
        unit_name=DENOMINATION_ASA_UNIT,
        asa_to_unit=1 / 10**DENOMINATION_ASA_DECIMALS,
    )
