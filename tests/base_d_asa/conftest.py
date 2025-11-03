from collections.abc import Callable
from typing import Final

import pytest
from algokit_utils import (
    AlgorandClient,
    AssetOptInParams,
    AssetTransferParams,
    CommonAppCallParams,
    SigningAccount,
)
from algokit_utils.config import config

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetConfigArgs,
    AssetCreateArgs,
    AssetMetadata,
    AssignRoleArgs,
    BaseDAsaClient,
    BaseDAsaFactory,
    OpenAccountArgs,
    PrimaryDistributionArgs,
    SetAssetSuspensionArgs,
    SetSecondaryTimeEventsArgs,
)
from tests import utils
from tests.conftest import (
    APR,
    INITIAL_ALGO_FUNDS,
    INITIAL_D_ASA_UNITS,
    ISSUANCE_DELAY,
    MATURITY_DELAY,
    MINIMUM_DENOMINATION,
    PRIMARY_DISTRIBUTION_DELAY,
    PRIMARY_DISTRIBUTION_DURATION,
    PRINCIPAL,
)

TOTAL_ASA_FUNDS: Final[int] = PRINCIPAL * (sc_cst.BPS + APR) // sc_cst.BPS
PROSPECTUS_URL: Final[str] = "Base D-ASA Prospectus"


@pytest.fixture(scope="session")
def asset_metadata() -> AssetMetadata:
    return AssetMetadata(
        contract_type=sc_cst.CT_PAM,
        calendar=sc_cst.CLDR_NC,
        business_day_convention=sc_cst.BDC_NOS,
        end_of_month_convention=sc_cst.EOMC_SD,
        prepayment_effect=sc_cst.PPEF_N,
        penalty_type=sc_cst.PYTP_N,
        prospectus_hash=bytes(32),
        prospectus_url=PROSPECTUS_URL,
    )


@pytest.fixture(scope="function")
def time_events(algorand: AlgorandClient) -> utils.TimeEvents:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    primary_distribution_opening = current_ts + PRIMARY_DISTRIBUTION_DELAY
    primary_distribution_closure = (
        primary_distribution_opening + PRIMARY_DISTRIBUTION_DURATION
    )
    issuance_date = primary_distribution_closure + ISSUANCE_DELAY
    maturity_date = issuance_date + MATURITY_DELAY
    return [
        primary_distribution_opening,
        primary_distribution_closure,
        issuance_date,
        maturity_date,
    ]


@pytest.fixture(scope="function")
def base_d_asa_cfg(
    currency: utils.Currency,
    time_events: utils.TimeEvents,
    day_count_convention: int,
) -> utils.DAsaConfig:
    return utils.DAsaConfig(
        denomination_asset_id=currency.id,
        settlement_asset_id=currency.id,
        principal=PRINCIPAL,
        principal_discount=0,
        minimum_denomination=MINIMUM_DENOMINATION,
        day_count_convention=day_count_convention,
        interest_rate=APR,
        coupon_rates=[],
        time_events=time_events,
        time_periods=[],
    )


@pytest.fixture(scope="function")
def base_d_asa_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    asset_metadata: AssetMetadata,
) -> BaseDAsaClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
        # trace_all=True,
    )

    factory = algorand.client.get_typed_app_factory(
        BaseDAsaFactory, default_sender=arranger.address, default_signer=arranger.signer
    )
    client, _ = factory.send.create.asset_create(
        AssetCreateArgs(arranger=arranger.address, metadata=asset_metadata)
    )
    algorand.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return client


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    base_d_asa_cfg: utils.DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> utils.DAsaAccountManager:
    account = algorand.account.random()
    account = utils.DAsaAccountManager(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    base_d_asa_client_empty.send.assign_role(
        AssignRoleArgs(
            role_address=account.address,
            role=account.role_id(),
            config=role_config,
        )
    )
    return account


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    base_d_asa_cfg: utils.DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> utils.DAsaAuthority:
    account = algorand.account.random()
    account = utils.DAsaAuthority(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    base_d_asa_client_empty.send.assign_role(
        AssignRoleArgs(
            role_address=account.address,
            role=account.role_id(),
            config=role_config,
        )
    )
    return account


@pytest.fixture(scope="function")
def base_d_asa_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    base_d_asa_cfg: utils.DAsaConfig,
    base_d_asa_client_empty: BaseDAsaClient,
) -> BaseDAsaClient:
    base_d_asa_client_empty.send.asset_config(
        AssetConfigArgs(**base_d_asa_cfg.dictify())
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            asset_id=base_d_asa_cfg.denomination_asset_id,
            amount=TOTAL_ASA_FUNDS,
            receiver=base_d_asa_client_empty.app_address,
            sender=bank.address,
            signer=bank.signer,
        )
    )

    return base_d_asa_client_empty


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient, base_d_asa_client_active: BaseDAsaClient
) -> utils.DAsaPrimaryDealer:
    account = algorand.account.random()
    account = utils.DAsaPrimaryDealer(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    state = base_d_asa_client_active.state.global_state
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    base_d_asa_client_active.send.assign_role(
        AssignRoleArgs(
            role_address=account.address,
            role=account.role_id(),
            config=role_config,
        )
    )
    return account


@pytest.fixture(scope="function")
def account_factory(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    account_manager: utils.DAsaAccountManager,
) -> Callable[..., utils.DAsaAccount]:
    def _factory(base_d_asa_client: BaseDAsaClient) -> utils.DAsaAccount:
        account = algorand.account.random()

        algorand.account.ensure_funded_from_environment(
            account_to_fund=account.address,
            min_spending_balance=INITIAL_ALGO_FUNDS,
        )

        algorand.send.asset_opt_in(
            AssetOptInParams(
                asset_id=currency.id,
                sender=account.address,
                signer=account.signer,
            )
        )

        base_d_asa_client.send.open_account(
            OpenAccountArgs(
                holding_address=account.address,
                payment_address=account.address,
            ),
            params=CommonAppCallParams(sender=account_manager.address),
        )
        return utils.DAsaAccount(
            d_asa_client=base_d_asa_client,
            holding_address=account.address,
            private_key=account.private_key,
        )

    return _factory


@pytest.fixture(scope="function")
def base_d_asa_client_primary(
    base_d_asa_client_active: BaseDAsaClient,
) -> BaseDAsaClient:
    state = base_d_asa_client_active.state.global_state
    base_d_asa_client_active.send.set_secondary_time_events(
        SetSecondaryTimeEventsArgs(
            secondary_market_time_events=[
                state.issuance_date,
                state.maturity_date,
            ]
        )
    )
    utils.time_warp(state.primary_distribution_opening_date)
    return base_d_asa_client_active


@pytest.fixture(scope="function")
def account_with_units_factory(
    account_factory: Callable[..., utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    base_d_asa_client_primary: BaseDAsaClient,
) -> Callable[..., utils.DAsaAccount]:
    def _factory(*, units: int = INITIAL_D_ASA_UNITS) -> utils.DAsaAccount:
        account = account_factory(base_d_asa_client_primary)
        base_d_asa_client_primary.send.primary_distribution(
            PrimaryDistributionArgs(
                holding_address=account.holding_address,
                units=units,
            ),
            params=CommonAppCallParams(sender=primary_dealer.address),
        )
        return account

    return _factory


@pytest.fixture(scope="function")
def account_a(
    account_with_units_factory: Callable[..., utils.DAsaAccount],
) -> utils.DAsaAccount:
    return account_with_units_factory()


@pytest.fixture(scope="function")
def base_d_asa_client_ongoing(
    base_d_asa_client_primary: BaseDAsaClient,
) -> BaseDAsaClient:
    state = base_d_asa_client_primary.state.global_state
    utils.time_warp(state.issuance_date)
    return base_d_asa_client_primary


@pytest.fixture(scope="function")
def base_d_asa_client_suspended(
    authority: utils.DAsaAuthority, base_d_asa_client_ongoing: BaseDAsaClient
) -> BaseDAsaClient:
    base_d_asa_client_ongoing.send.set_asset_suspension(
        SetAssetSuspensionArgs(suspended=True),
        params=CommonAppCallParams(sender=authority.address),
    )
    return base_d_asa_client_ongoing
