from collections.abc import Callable
from typing import Final

import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AccountOpenArgs,
    AssetConfigArgs,
    AssetCreateArgs,
    AssetMetadata,
    FixedCouponBondClient,
    FixedCouponBondFactory,
    PayCouponArgs,
    PrimaryDistributionArgs,
    RbacAssignRoleArgs,
    RbacGovAssetSuspensionArgs,
    SetDefaultStatusArgs,
    SetSecondaryTimeEventsArgs,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests import conftest_helpers as helpers
from tests import utils
from tests.conftest import (
    APR,
    INITIAL_D_ASA_UNITS,
    ISSUANCE_DELAY,
    MATURITY_DELAY,
    MINIMUM_DENOMINATION,
    PRIMARY_DISTRIBUTION_DELAY,
    PRIMARY_DISTRIBUTION_DURATION,
    PRINCIPAL,
)

TOTAL_COUPONS: Final[int] = 2  # Max 120
COUPON_RATE: Final[int] = APR // TOTAL_COUPONS
COUPON_RATE_INCREASE: Final[int] = 5  # BPS equal to 0.05%
COUPON_RATES: Final[list[int]] = [
    COUPON_RATE + i * COUPON_RATE_INCREASE for i in range(TOTAL_COUPONS)
]
INTEREST_RATE = sum(COUPON_RATES)
COUPON_PERIOD: Final[int] = 30 * sc_cst.DAY_2_SEC

TOTAL_ASA_FUNDS: Final[int] = PRINCIPAL * (sc_cst.BPS + INTEREST_RATE) // sc_cst.BPS

PROSPECTUS_URL: Final[str] = "Fixed Coupon Bond Prospectus"


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


@pytest.fixture(scope="session")
def coupon_rates() -> utils.CouponRates:
    return COUPON_RATES


@pytest.fixture(scope="function")
def time_events(algorand: AlgorandClient) -> utils.TimeEvents:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    primary_distribution_opening = current_ts + PRIMARY_DISTRIBUTION_DELAY
    primary_distribution_closure = (
        primary_distribution_opening + PRIMARY_DISTRIBUTION_DURATION
    )
    issuance_date = primary_distribution_closure + ISSUANCE_DELAY
    coupon_dates = [
        issuance_date + i * COUPON_PERIOD for i in range(1, TOTAL_COUPONS + 1)
    ]
    maturity_date = coupon_dates[-1] + MATURITY_DELAY
    return [
        primary_distribution_opening,
        primary_distribution_closure,
        issuance_date,
        *coupon_dates,
        maturity_date,
    ]


@pytest.fixture(scope="function")
def fixed_coupon_bond_cfg(
    currency: utils.Currency,
    coupon_rates: utils.CouponRates,
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
        interest_rate=INTEREST_RATE,
        coupon_rates=coupon_rates,
        time_events=time_events,
        time_periods=[],
    )


@pytest.fixture(scope="function")
def fixed_coupon_bond_client_empty(
    algorand: AlgorandClient,
    arranger: SigningAccount,
    asset_metadata: AssetMetadata,
) -> FixedCouponBondClient:
    return helpers.create_and_fund_client(
        algorand,
        FixedCouponBondFactory,
        arranger,
        AssetCreateArgs(arranger=arranger.address, metadata=asset_metadata),
    )


@pytest.fixture(scope="function")
def account_manager(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: utils.DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> utils.DAsaAccountManager:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        fixed_coupon_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def trustee(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: utils.DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> utils.DAsaTrustee:
    return helpers.create_role_account(
        algorand,
        utils.DAsaTrustee,
        fixed_coupon_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def authority(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: utils.DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> utils.DAsaAuthority:
    return helpers.create_role_account(
        algorand,
        utils.DAsaAuthority,
        fixed_coupon_bond_client_empty,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )


@pytest.fixture(scope="function")
def fixed_coupon_bond_client_active(
    algorand: AlgorandClient,
    bank: SigningAccount,
    fixed_coupon_bond_cfg: utils.DAsaConfig,
    fixed_coupon_bond_client_empty: FixedCouponBondClient,
) -> FixedCouponBondClient:
    return helpers.activate_client_with_config_and_funding(
        algorand,
        fixed_coupon_bond_client_empty,
        bank,
        fixed_coupon_bond_cfg,
        TOTAL_ASA_FUNDS,
        AssetConfigArgs,
    )


@pytest.fixture(scope="function")
def primary_dealer(
    algorand: AlgorandClient,
    fixed_coupon_bond_client_active: FixedCouponBondClient,
) -> utils.DAsaPrimaryDealer:
    state = fixed_coupon_bond_client_active.state.global_state
    role_config = utils.set_role_config(
        state.primary_distribution_opening_date, state.primary_distribution_closure_date
    )
    return helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        fixed_coupon_bond_client_active,
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
def fixed_coupon_bond_client_primary(
    fixed_coupon_bond_client_active: FixedCouponBondClient,
) -> FixedCouponBondClient:
    state = fixed_coupon_bond_client_active.state.global_state
    return helpers.set_client_to_primary_phase(
        fixed_coupon_bond_client_active,
        SetSecondaryTimeEventsArgs,
        [state.issuance_date, state.maturity_date],
    )


@pytest.fixture(scope="function")
def account_with_units_factory(
    account_factory: Callable[..., utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> Callable[..., utils.DAsaAccount]:
    return helpers.build_account_with_units_factory(
        account_factory,
        primary_dealer,
        fixed_coupon_bond_client_primary,
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
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> Callable[..., utils.DAsaAccount]:
    state = fixed_coupon_bond_client_primary.state.global_state

    def _factory(
        *, units: int = INITIAL_D_ASA_UNITS, coupons: int = state.total_coupons
    ) -> utils.DAsaAccount:
        account = account_with_units_factory(units=units)
        time_events = fixed_coupon_bond_client_primary.send.get_time_events().abi_return
        utils.time_warp(time_events[sc_cfg.FIRST_COUPON_DATE_IDX + coupons - 1])
        for _ in range(1, coupons + 1):
            fixed_coupon_bond_client_primary.send.pay_coupon(
                PayCouponArgs(
                    holding_address=account.holding_address,
                    payment_info=b"",
                ),
                params=CommonAppCallParams(max_fee=utils.max_fee_per_coupon(coupons)),
                send_params=SendParams(cover_app_call_inner_transaction_fees=True),
            )
        return account

    return _factory


@pytest.fixture(scope="function")
def fixed_coupon_bond_client_ongoing(
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> FixedCouponBondClient:
    state = fixed_coupon_bond_client_primary.state.global_state
    utils.time_warp(state.issuance_date)
    return fixed_coupon_bond_client_primary


@pytest.fixture(scope="function")
def fixed_coupon_bond_client_at_maturity(
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> FixedCouponBondClient:
    state = fixed_coupon_bond_client_ongoing.state.global_state
    utils.time_warp(state.maturity_date)
    return fixed_coupon_bond_client_ongoing


@pytest.fixture(scope="function")
def fixed_coupon_bond_client_suspended(
    authority: utils.DAsaAuthority,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> FixedCouponBondClient:
    return helpers.suspend_client(
        fixed_coupon_bond_client_ongoing, authority, RbacGovAssetSuspensionArgs
    )


@pytest.fixture(scope="function")
def fixed_coupon_bond_client_defaulted(
    trustee: utils.DAsaTrustee, fixed_coupon_bond_client_ongoing: FixedCouponBondClient
) -> FixedCouponBondClient:
    return helpers.set_client_to_default(
        fixed_coupon_bond_client_ongoing, trustee, SetDefaultStatusArgs
    )
