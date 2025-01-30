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
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetMetadata,
    PerpetualBondClient,
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

COUPON_PERIOD: Final[int] = 360 * sc_cst.DAY_2_SEC
DUE_COUPONS: Final[int] = 4

TOTAL_ASA_FUNDS: Final[int] = PRINCIPAL * (sc_cst.BPS + APR) // sc_cst.BPS

PROSPECTUS_URL: Final[str] = "Perpetual Bond Prospectus"


@pytest.fixture(scope="function")
def time_events(algorand: AlgorandClient) -> utils.TimeEvents:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    primary_distribution_opening = current_ts + PRIMARY_DISTRIBUTION_DELAY
    primary_distribution_closure = (
        primary_distribution_opening + PRIMARY_DISTRIBUTION_DURATION
    )
    issuance_date = primary_distribution_closure + ISSUANCE_DELAY
    return [
        primary_distribution_opening,
        primary_distribution_closure,
        issuance_date,
    ]


@pytest.fixture(scope="session")
def asset_metadata() -> AssetMetadata:
    return AssetMetadata(
        contract_type=sc_cst.CT_PBN,
        calendar=sc_cst.CLDR_NC,
        business_day_convention=sc_cst.BDC_NOS,
        end_of_month_convention=sc_cst.EOMC_SD,
        prepayment_effect=sc_cst.PPEF_N,
        penalty_type=sc_cst.PYTP_N,
        prospectus_hash=bytes(32),
        prospectus_url=PROSPECTUS_URL,
    )


@pytest.fixture(scope="function")
def perpetual_bond_cfg(
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
        time_periods=[(COUPON_PERIOD, 0)],
    )


@pytest.fixture(scope="function")
def perpetual_bond_client_void(
    algorand: AlgorandClient, arranger: SigningAccount
) -> PerpetualBondClient:
    config.configure(
        debug=False,
        # trace_all=True,
    )

    client = PerpetualBondClient(
        algorand.client.algod,
        creator=arranger.address,
        signer=arranger.signer,
        indexer_client=algorand.client.indexer,
    )
    return client


@pytest.fixture(scope="function")
def perpetual_bond_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    asset_metadata: AssetMetadata,
    perpetual_bond_client_void: PerpetualBondClient,
) -> PerpetualBondClient:
    perpetual_bond_client_void.create_asset_create(
        arranger=arranger.address, metadata=asset_metadata
    )
    algorand.account.ensure_funded_from_environment(
        account_to_fund=perpetual_bond_client_void.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return perpetual_bond_client_void


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaAccountManager:
    account = algorand.account.random()
    account = utils.DAsaAccountManager(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    perpetual_bond_client_empty.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def trustee(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaTrustee:
    account = algorand.account.random()
    account = utils.DAsaTrustee(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    perpetual_bond_client_empty.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaAuthority:
    account = algorand.account.random()
    account = utils.DAsaAuthority(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    perpetual_bond_client_empty.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def interest_oracle(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaInterestOracle:
    account = algorand.account.random()
    account = utils.DAsaInterestOracle(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    role_config = utils.set_role_config()
    perpetual_bond_client_empty.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_empty.app_id, account.box_id)]
        ),
    )
    return account


@pytest.fixture(scope="function")
def perpetual_bond_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> PerpetualBondClient:
    perpetual_bond_client_empty.asset_config(
        **perpetual_bond_cfg.dictify(),
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[perpetual_bond_cfg.denomination_asset_id],
            boxes=[
                (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS),
                (perpetual_bond_client_empty.app_id, sc_cst.BOX_ID_TIME_PERIODS),
            ],
        ),
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            asset_id=perpetual_bond_cfg.denomination_asset_id,
            amount=TOTAL_ASA_FUNDS,
            receiver=perpetual_bond_client_empty.app_address,
            sender=bank.address,
            signer=bank.signer,
        )
    )

    return perpetual_bond_client_empty


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient,
    perpetual_bond_client_active: PerpetualBondClient,
) -> utils.DAsaPrimaryDealer:
    account = algorand.account.random()
    account = utils.DAsaPrimaryDealer(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    state = perpetual_bond_client_active.get_global_state()
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    perpetual_bond_client_active.assign_role(
        role_address=account.address,
        role=account.role_id(),
        config=role_config,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(perpetual_bond_client_active.app_id, account.box_id)]
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
    def _factory(perpetual_bond_client: PerpetualBondClient) -> utils.DAsaAccount:
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

        perpetual_bond_client.open_account(
            holding_address=account.address,
            payment_address=account.address,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_manager.signer,
                boxes=[
                    (perpetual_bond_client.app_id, account_manager.box_id),
                    (
                        perpetual_bond_client.app_id,
                        utils.DAsaAccount.box_id_from_address(account.address),
                    ),
                ],
            ),
        )
        return utils.DAsaAccount(
            d_asa_client=perpetual_bond_client,
            holding_address=account.address,
            private_key=account.private_key,
        )

    return _factory


@pytest.fixture(scope="function")
def perpetual_bond_client_primary(
    perpetual_bond_client_active: PerpetualBondClient,
) -> PerpetualBondClient:
    state = perpetual_bond_client_active.get_global_state()
    perpetual_bond_client_active.set_secondary_time_events(
        secondary_market_time_events=[state.issuance_date],
    )
    utils.time_warp(state.primary_distribution_opening_date)
    return perpetual_bond_client_active


@pytest.fixture(scope="function")
def account_with_units_factory(
    account_factory: Callable[..., utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    perpetual_bond_client_primary: PerpetualBondClient,
) -> Callable[..., utils.DAsaAccount]:
    def _factory(*, units: int = INITIAL_D_ASA_UNITS) -> utils.DAsaAccount:
        account = account_factory(perpetual_bond_client_primary)
        perpetual_bond_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=units,
            transaction_parameters=OnCompleteCallParameters(
                signer=primary_dealer.signer,
                boxes=[
                    (perpetual_bond_client_primary.app_id, primary_dealer.box_id),
                    (perpetual_bond_client_primary.app_id, account.box_id),
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
def account_with_coupons_factory(
    account_with_units_factory: Callable[..., utils.DAsaAccount],
    perpetual_bond_client_primary: PerpetualBondClient,
) -> Callable[..., utils.DAsaAccount]:
    state = perpetual_bond_client_primary.get_global_state()

    def _factory(
        *, units: int = INITIAL_D_ASA_UNITS, coupons: int = DUE_COUPONS
    ) -> utils.DAsaAccount:
        account = account_with_units_factory(units=units)
        issuance_date = state.issuance_date
        utils.time_warp(issuance_date + COUPON_PERIOD * coupons)
        for _ in range(1, coupons + 1):
            perpetual_bond_client_primary.pay_coupon(
                holding_address=account.holding_address,
                payment_info=b"",
                transaction_parameters=OnCompleteCallParameters(
                    foreign_assets=[state.denomination_asset_id],
                    accounts=[account.payment_address],
                    boxes=[(perpetual_bond_client_primary.app_id, account.box_id)],
                ),
            )
        return account

    return _factory


@pytest.fixture(scope="function")
def perpetual_bond_client_ongoing(
    perpetual_bond_client_primary: PerpetualBondClient,
) -> PerpetualBondClient:
    state = perpetual_bond_client_primary.get_global_state()
    utils.time_warp(state.issuance_date)
    return perpetual_bond_client_primary


@pytest.fixture(scope="function")
def perpetual_bond_client_suspended(
    authority: utils.DAsaAuthority,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> PerpetualBondClient:
    perpetual_bond_client_ongoing.set_asset_suspension(
        suspended=True,
        transaction_parameters=OnCompleteCallParameters(
            signer=authority.signer,
            boxes=[(perpetual_bond_client_ongoing.app_id, authority.box_id)],
        ),
    )
    return perpetual_bond_client_ongoing


@pytest.fixture(scope="function")
def perpetual_bond_client_defaulted(
    trustee: utils.DAsaTrustee, perpetual_bond_client_ongoing: PerpetualBondClient
) -> PerpetualBondClient:
    perpetual_bond_client_ongoing.set_default_status(
        defaulted=True,
        transaction_parameters=OnCompleteCallParameters(
            signer=trustee.signer,
            boxes=[(perpetual_bond_client_ongoing.app_id, trustee.box_id)],
        ),
    )
    return perpetual_bond_client_ongoing
