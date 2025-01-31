from typing import Callable, Final

import pytest
from algokit_utils import (
    AlgorandClient,
    AssetOptInParams,
    AssetTransferParams,
    OnCompleteCallParameters,
    SigningAccount,
)
from algokit_utils.config import config

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetMetadata,
    ZeroCouponBondClient,
)
from tests import utils
from tests.conftest import (
    APR,
    INITIAL_ALGO_FUNDS,
    INITIAL_D_ASA_UNITS,
    ISSUANCE_DELAY,
    MINIMUM_DENOMINATION,
    PRIMARY_DISTRIBUTION_DELAY,
    PRIMARY_DISTRIBUTION_DURATION,
    PRINCIPAL,
)

MATURITY_DELAY: Final[int] = 366 * sc_cst.DAY_2_SEC
TOTAL_ASA_FUNDS: Final[int] = PRINCIPAL * (sc_cst.BPS + APR) // sc_cst.BPS

PROSPECTUS_URL: Final[str] = "Zero Coupon Bond Prospectus"


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
def time_events(
    algorand: AlgorandClient,
) -> utils.TimeEvents:
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
def zero_coupon_bond_cfg(
    currency: utils.Currency,
    time_events: utils.TimeEvents,
    day_count_convention: int,
) -> utils.DAsaConfig:
    return utils.DAsaConfig(
        denomination_asset_id=currency.id,
        settlement_asset_id=currency.id,
        principal=PRINCIPAL,
        principal_discount=APR,
        minimum_denomination=MINIMUM_DENOMINATION,
        day_count_convention=day_count_convention,
        interest_rate=0,
        coupon_rates=[],
        time_events=time_events,
        time_periods=[],
    )


@pytest.fixture(scope="function")
def zero_coupon_bond_client_void(
    algorand: AlgorandClient, arranger: SigningAccount
) -> ZeroCouponBondClient:
    config.configure(
        debug=False,
        # trace_all=True,
    )

    client = ZeroCouponBondClient(
        algorand.client.algod,
        creator=arranger.address,
        signer=arranger.signer,
        indexer_client=algorand.client.indexer,
    )
    return client


@pytest.fixture(scope="function")
def zero_coupon_bond_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    asset_metadata: AssetMetadata,
    zero_coupon_bond_client_void: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    zero_coupon_bond_client_void.create_asset_create(
        arranger=arranger.address, metadata=asset_metadata
    )
    algorand.account.ensure_funded_from_environment(
        account_to_fund=zero_coupon_bond_client_void.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return zero_coupon_bond_client_void


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    zero_coupon_bond_cfg: utils.DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> utils.DAsaAccountManager:
    account = algorand.account.random()
    account = utils.DAsaAccountManager(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    zero_coupon_bond_client_empty.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(zero_coupon_bond_client_empty.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    zero_coupon_bond_cfg: utils.DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> utils.DAsaAuthority:
    account = algorand.account.random()
    account = utils.DAsaAuthority(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    zero_coupon_bond_client_empty.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(zero_coupon_bond_client_empty.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def zero_coupon_bond_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    zero_coupon_bond_cfg: utils.DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    zero_coupon_bond_client_empty.asset_config(
        **zero_coupon_bond_cfg.dictify(),
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[zero_coupon_bond_cfg.denomination_asset_id],
            boxes=[
                (zero_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (zero_coupon_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            asset_id=zero_coupon_bond_cfg.denomination_asset_id,
            amount=TOTAL_ASA_FUNDS,
            receiver=zero_coupon_bond_client_empty.app_address,
            sender=bank.address,
            signer=bank.signer,
        )
    )

    return zero_coupon_bond_client_empty


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient,
    zero_coupon_bond_client_active: ZeroCouponBondClient,
) -> utils.DAsaPrimaryDealer:
    account = algorand.account.random()
    account = utils.DAsaPrimaryDealer(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    state = zero_coupon_bond_client_active.get_global_state()
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    zero_coupon_bond_client_active.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(zero_coupon_bond_client_active.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def account_factory(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    account_manager: utils.DAsaAccountManager,
) -> Callable[..., utils.DAsaAccount]:
    def _factory(base_d_asa_client: ZeroCouponBondClient) -> utils.DAsaAccount:
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

        base_d_asa_client.open_account(
            holding_address=account.address,
            payment_address=account.address,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_manager.signer,
                boxes=[
                    (base_d_asa_client.app_id, account_manager.box_id),
                    (
                        base_d_asa_client.app_id,
                        utils.DAsaAccount.box_id_from_address(account.address),
                    ),
                ],
            ),
        )
        return utils.DAsaAccount(
            d_asa_client=base_d_asa_client,
            holding_address=account.address,
            private_key=account.private_key,
        )

    return _factory


@pytest.fixture(scope="function")
def zero_coupon_bond_client_primary(
    zero_coupon_bond_client_active: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    state = zero_coupon_bond_client_active.get_global_state()
    zero_coupon_bond_client_active.set_secondary_time_events(
        secondary_market_time_events=[state.issuance_date, state.maturity_date],
    )
    utils.time_warp(state.primary_distribution_opening_date)
    return zero_coupon_bond_client_active


@pytest.fixture(scope="function")
def account_with_units_factory(
    account_factory: Callable[..., utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
) -> Callable[..., utils.DAsaAccount]:
    def _factory(*, units: int = INITIAL_D_ASA_UNITS) -> utils.DAsaAccount:
        account = account_factory(zero_coupon_bond_client_primary)
        zero_coupon_bond_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=units,
            transaction_parameters=OnCompleteCallParameters(
                signer=primary_dealer.signer,
                boxes=[
                    (zero_coupon_bond_client_primary.app_id, primary_dealer.box_id),
                    (zero_coupon_bond_client_primary.app_id, account.box_id),
                ],
            ),
        )
        return account

    return _factory


@pytest.fixture(scope="function")
def account_a(
    account_with_units_factory: Callable[..., utils.DAsaAccount]
) -> utils.DAsaAccount:
    return account_with_units_factory()


@pytest.fixture(scope="function")
def account_b(
    account_with_units_factory: Callable[..., utils.DAsaAccount]
) -> utils.DAsaAccount:
    return account_with_units_factory(units=2 * INITIAL_D_ASA_UNITS)


@pytest.fixture(scope="function")
def zero_coupon_bond_client_ongoing(
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    state = zero_coupon_bond_client_primary.get_global_state()
    utils.time_warp(state.issuance_date)
    return zero_coupon_bond_client_primary


@pytest.fixture(scope="function")
def zero_coupon_bond_client_at_maturity(
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    state = zero_coupon_bond_client_ongoing.get_global_state()
    utils.time_warp(state.maturity_date)
    return zero_coupon_bond_client_ongoing


@pytest.fixture(scope="function")
def zero_coupon_bond_client_suspended(
    authority: utils.DAsaAuthority,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    zero_coupon_bond_client_ongoing.set_asset_suspension(
        suspended=True,
        transaction_parameters=OnCompleteCallParameters(
            signer=authority.signer,
            boxes=[(zero_coupon_bond_client_ongoing.app_id, authority.box_id)],
        ),
    )
    return zero_coupon_bond_client_ongoing
