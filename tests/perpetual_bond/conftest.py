from typing import Callable, Final

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
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetConfigArgs,
    AssetCreateArgs,
    AssetMetadata,
    AssignRoleArgs,
    OpenAccountArgs,
    PayCouponArgs,
    PerpetualBondClient,
    PerpetualBondFactory,
    PrimaryDistributionArgs,
    SetAssetSuspensionArgs,
    SetDefaultStatusArgs,
    SetSecondaryTimeEventsArgs,
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
def perpetual_bond_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    asset_metadata: AssetMetadata,
) -> PerpetualBondClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
        # trace_all=True,
    )

    factory = algorand.client.get_typed_app_factory(
        PerpetualBondFactory,
        default_sender=arranger.address,
        default_signer=arranger.signer,
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
    perpetual_bond_client_empty.send.assign_role(
        AssignRoleArgs(
            role_address=account.address,
            role=account.role_id(),
            config=role_config,
        )
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
    perpetual_bond_client_empty.send.assign_role(
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
    perpetual_bond_client_empty.send.assign_role(
        AssignRoleArgs(
            role_address=account.address,
            role=account.role_id(),
            config=role_config,
        )
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
    perpetual_bond_client_empty.send.assign_role(
        AssignRoleArgs(
            role_address=account.address,
            role=account.role_id(),
            config=role_config,
        )
    )
    return account


@pytest.fixture(scope="function")
def perpetual_bond_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> PerpetualBondClient:
    perpetual_bond_client_empty.send.asset_config(
        AssetConfigArgs(**perpetual_bond_cfg.dictify())
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
    state = perpetual_bond_client_active.state.global_state
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    perpetual_bond_client_active.send.assign_role(
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

        perpetual_bond_client.send.open_account(
            OpenAccountArgs(
                holding_address=account.address,
                payment_address=account.address,
            ),
            params=CommonAppCallParams(sender=account_manager.address),
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
    state = perpetual_bond_client_active.state.global_state
    perpetual_bond_client_active.send.set_secondary_time_events(
        SetSecondaryTimeEventsArgs(secondary_market_time_events=[state.issuance_date]),
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
        perpetual_bond_client_primary.send.primary_distribution(
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
def account_b(
    account_with_units_factory: Callable[..., utils.DAsaAccount],
) -> utils.DAsaAccount:
    return account_with_units_factory(units=2 * INITIAL_D_ASA_UNITS)


@pytest.fixture(scope="function")
def account_with_coupons_factory(
    account_with_units_factory: Callable[..., utils.DAsaAccount],
    perpetual_bond_client_primary: PerpetualBondClient,
) -> Callable[..., utils.DAsaAccount]:
    state = perpetual_bond_client_primary.state.global_state

    def _factory(
        *, units: int = INITIAL_D_ASA_UNITS, coupons: int = DUE_COUPONS
    ) -> utils.DAsaAccount:
        account = account_with_units_factory(units=units)
        issuance_date = state.issuance_date
        utils.time_warp(issuance_date + COUPON_PERIOD * coupons)
        for _ in range(1, coupons + 1):
            perpetual_bond_client_primary.send.pay_coupon(
                PayCouponArgs(
                    holding_address=account.holding_address,
                    payment_info=b"",
                )
            )
        return account

    return _factory


@pytest.fixture(scope="function")
def perpetual_bond_client_ongoing(
    perpetual_bond_client_primary: PerpetualBondClient,
) -> PerpetualBondClient:
    state = perpetual_bond_client_primary.state.global_state
    utils.time_warp(state.issuance_date)
    return perpetual_bond_client_primary


@pytest.fixture(scope="function")
def perpetual_bond_client_suspended(
    authority: utils.DAsaAuthority,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> PerpetualBondClient:
    perpetual_bond_client_ongoing.send.set_asset_suspension(
        SetAssetSuspensionArgs(suspended=True)
    )
    return perpetual_bond_client_ongoing


@pytest.fixture(scope="function")
def perpetual_bond_client_defaulted(
    trustee: utils.DAsaTrustee, perpetual_bond_client_ongoing: PerpetualBondClient
) -> PerpetualBondClient:
    perpetual_bond_client_ongoing.send.set_default_status(
        SetDefaultStatusArgs(defaulted=True)
    )
    return perpetual_bond_client_ongoing
