from collections.abc import Callable
from typing import Final

import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AccountOpenArgs,
    AssetConfigArgs,
    AssetCreateArgs,
    AssetMetadata,
    PayCouponArgs,
    PerpetualBondClient,
    PerpetualBondFactory,
    PrimaryDistributionArgs,
    RbacAssignRoleArgs,
    RbacGovAssetSuspensionArgs,
    SetDefaultStatusArgs,
    SetSecondaryTimeEventsArgs,
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
    return helpers.create_and_fund_client(
        algorand,
        PerpetualBondFactory,
        arranger,
        AssetCreateArgs(arranger=arranger.address, metadata=asset_metadata),
    )


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        perpetual_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def trustee(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaTrustee:
    return helpers.create_role_account(
        algorand,
        utils.DAsaTrustee,
        perpetual_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaAuthority:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        perpetual_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def interest_oracle(
    algorand: AlgorandClient,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> utils.DAsaInterestOracle:
    return helpers.create_role_account(
        algorand,
        utils.DAsaInterestOracle,
        perpetual_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def perpetual_bond_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    perpetual_bond_cfg: utils.DAsaConfig,
    perpetual_bond_client_empty: PerpetualBondClient,
) -> PerpetualBondClient:
    return helpers.activate_client_with_config_and_funding(
        algorand,
        perpetual_bond_client_empty,
        bank,
        perpetual_bond_cfg,
        TOTAL_ASA_FUNDS,
        AssetConfigArgs,
    )


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient,
    perpetual_bond_client_active: PerpetualBondClient,
) -> utils.DAsaPrimaryDealer:
    state = perpetual_bond_client_active.state.global_state
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    return helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        perpetual_bond_client_active,
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
def perpetual_bond_client_primary(
    perpetual_bond_client_active: PerpetualBondClient,
) -> PerpetualBondClient:
    state = perpetual_bond_client_active.state.global_state
    return helpers.set_client_to_primary_phase(
        perpetual_bond_client_active,
        SetSecondaryTimeEventsArgs,
        [state.issuance_date],
    )


@pytest.fixture(scope="function")
def account_with_units_factory(
    account_factory: Callable[..., utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    perpetual_bond_client_primary: PerpetualBondClient,
) -> Callable[..., utils.DAsaAccount]:
    return helpers.build_account_with_units_factory(
        account_factory,
        primary_dealer,
        perpetual_bond_client_primary,
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
    return helpers.suspend_client(
        perpetual_bond_client_ongoing, authority, RbacGovAssetSuspensionArgs
    )


@pytest.fixture(scope="function")
def perpetual_bond_client_defaulted(
    trustee: utils.DAsaTrustee, perpetual_bond_client_ongoing: PerpetualBondClient
) -> PerpetualBondClient:
    return helpers.set_client_to_default(
        perpetual_bond_client_ongoing, trustee, SetDefaultStatusArgs
    )
