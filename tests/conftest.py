from typing import Final

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AssetCreateParams,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from tests import utils

INITIAL_ALGO_FUNDS: Final[AlgoAmount] = AlgoAmount({"algos": 10_000})

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
def algorand() -> AlgorandClient:
    client = AlgorandClient.default_localnet()
    client.set_suggested_params_timeout(0)
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
def oscar(algorand: AlgorandClient) -> SigningAccount:
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


@pytest.fixture(scope="function", params=DAY_COUNT_CONVENTION)
def day_count_convention(request) -> int:  # noqa: ANN001
    return request.param
