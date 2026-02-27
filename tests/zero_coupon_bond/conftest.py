from collections.abc import Callable
from typing import Final

import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AccountOpenArgs,
    AssetConfigArgs,
    AssetCreateArgs,
    AssetMetadata,
    PrimaryDistributionArgs,
    RbacAssignRoleArgs,
    RbacGovAssetSuspensionArgs,
    SetSecondaryTimeEventsArgs,
    ZeroCouponBondClient,
    ZeroCouponBondFactory,
)
from tests import conftest_helpers as helpers
from tests import utils
from tests.conftest import (
    APR,
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
def zero_coupon_bond_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    asset_metadata: AssetMetadata,
) -> ZeroCouponBondClient:
    return helpers.create_and_fund_client(
        algorand,
        ZeroCouponBondFactory,
        arranger,
        AssetCreateArgs(arranger=arranger.address, metadata=asset_metadata),
    )


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    zero_coupon_bond_cfg: utils.DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        zero_coupon_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    zero_coupon_bond_cfg: utils.DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> utils.DAsaAuthority:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        zero_coupon_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def zero_coupon_bond_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    zero_coupon_bond_cfg: utils.DAsaConfig,
    zero_coupon_bond_client_empty: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    return helpers.activate_client_with_config_and_funding(
        algorand,
        zero_coupon_bond_client_empty,
        bank,
        zero_coupon_bond_cfg,
        TOTAL_ASA_FUNDS,
        AssetConfigArgs,
    )


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient,
    zero_coupon_bond_client_active: ZeroCouponBondClient,
) -> utils.DAsaPrimaryDealer:
    state = zero_coupon_bond_client_active.state.global_state
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    return helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        zero_coupon_bond_client_active,
        role_config,
        RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def account_factory(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    account_manager: utils.DAsaAccountManager,
) -> Callable[..., utils.DAsaAccount]:
    return helpers.build_account_factory(
        algorand, currency, account_manager, AccountOpenArgs
    )


@pytest.fixture(scope="function")
def zero_coupon_bond_client_primary(
    zero_coupon_bond_client_active: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    state = zero_coupon_bond_client_active.state.global_state
    return helpers.set_client_to_primary_phase(
        zero_coupon_bond_client_active,
        SetSecondaryTimeEventsArgs,
        [state.issuance_date, state.maturity_date],
    )


@pytest.fixture(scope="function")
def account_with_units_factory(
    account_factory: Callable[..., utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
) -> Callable[..., utils.DAsaAccount]:
    return helpers.build_account_with_units_factory(
        account_factory,
        primary_dealer,
        zero_coupon_bond_client_primary,
        PrimaryDistributionArgs,
        INITIAL_D_ASA_UNITS,
    )


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
def zero_coupon_bond_client_ongoing(
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    state = zero_coupon_bond_client_primary.state.global_state
    utils.time_warp(state.issuance_date)
    return zero_coupon_bond_client_primary


@pytest.fixture(scope="function")
def zero_coupon_bond_client_at_maturity(
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    state = zero_coupon_bond_client_ongoing.state.global_state
    utils.time_warp(state.maturity_date)
    return zero_coupon_bond_client_ongoing


@pytest.fixture(scope="function")
def zero_coupon_bond_client_suspended(
    authority: utils.DAsaAuthority,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> ZeroCouponBondClient:
    return helpers.suspend_client(
        zero_coupon_bond_client_ongoing, authority, RbacGovAssetSuspensionArgs
    )
