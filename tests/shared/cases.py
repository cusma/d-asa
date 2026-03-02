from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AccountOpenArgs as FixedAccountOpenArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AssetConfigArgs as FixedAssetConfigArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AssetCreateArgs as FixedAssetCreateArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AssetMetadata as FixedAssetMetadata,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AssetUpdateArgs as FixedAssetUpdateArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondFactory,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    PrimaryDistributionArgs as FixedPrimaryDistributionArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    RbacAssignRoleArgs as FixedRbacAssignRoleArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    RbacGovAssetSuspensionArgs as FixedRbacGovAssetSuspensionArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    SetDefaultStatusArgs as FixedSetDefaultStatusArgs,
)
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    SetSecondaryTimeEventsArgs as FixedSetSecondaryTimeEventsArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AccountOpenArgs as PerpetualAccountOpenArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetConfigArgs as PerpetualAssetConfigArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetCreateArgs as PerpetualAssetCreateArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetMetadata as PerpetualAssetMetadata,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AssetUpdateArgs as PerpetualAssetUpdateArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PerpetualBondFactory,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    PrimaryDistributionArgs as PerpetualPrimaryDistributionArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    RbacAssignRoleArgs as PerpetualRbacAssignRoleArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    RbacGovAssetSuspensionArgs as PerpetualRbacGovAssetSuspensionArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    SetDefaultStatusArgs as PerpetualSetDefaultStatusArgs,
)
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    SetSecondaryTimeEventsArgs as PerpetualSetSecondaryTimeEventsArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AccountOpenArgs as ZeroAccountOpenArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetConfigArgs as ZeroAssetConfigArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetCreateArgs as ZeroAssetCreateArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetMetadata as ZeroAssetMetadata,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetUpdateArgs as ZeroAssetUpdateArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    PrimaryDistributionArgs as ZeroPrimaryDistributionArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    RbacAssignRoleArgs as ZeroRbacAssignRoleArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    RbacGovAssetSuspensionArgs as ZeroRbacGovAssetSuspensionArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    SetDefaultStatusArgs as ZeroSetDefaultStatusArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    SetSecondaryTimeEventsArgs as ZeroSetSecondaryTimeEventsArgs,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    ZeroCouponBondFactory,
)
from tests import utils
from tests.conftest import (
    APR,
    ISSUANCE_DELAY,
    MATURITY_DELAY,
    MINIMUM_DENOMINATION,
    PRIMARY_DISTRIBUTION_DELAY,
    PRIMARY_DISTRIBUTION_DURATION,
    PRINCIPAL,
)

_FIXED_TOTAL_COUPONS = 2
_FIXED_COUPON_RATE = APR // _FIXED_TOTAL_COUPONS
_FIXED_COUPON_RATE_INCREASE = 5
_FIXED_COUPON_RATES = [
    _FIXED_COUPON_RATE + idx * _FIXED_COUPON_RATE_INCREASE
    for idx in range(_FIXED_TOTAL_COUPONS)
]
_FIXED_INTEREST_RATE = sum(_FIXED_COUPON_RATES)
_FIXED_COUPON_PERIOD = 30 * sc_cst.DAY_2_SEC

_ZERO_MATURITY_DELAY = 366 * sc_cst.DAY_2_SEC
_PERPETUAL_COUPON_PERIOD = 360 * sc_cst.DAY_2_SEC


@dataclass(frozen=True)
class ContractCapabilities:
    has_maturity: bool
    has_coupon: bool
    has_principal: bool
    has_time_periods: bool
    has_coupon_rates: bool


@dataclass(frozen=True)
class ContractCase:
    name: str
    metadata_contract_type: int
    prospectus_url: str
    factory_class: Any
    asset_metadata_cls: Any
    asset_create_args_cls: Any
    asset_config_args_cls: Any
    asset_update_args_cls: Any
    account_open_args_cls: Any
    primary_distribution_args_cls: Any
    set_secondary_time_events_args_cls: Any
    rbac_assign_role_args_cls: Any
    rbac_gov_asset_suspension_args_cls: Any
    set_default_status_args_cls: Any
    capabilities: ContractCapabilities
    build_time_events: Callable[[int], utils.TimeEvents]
    build_config: Callable[[utils.Currency, utils.TimeEvents, int], utils.DAsaConfig]
    secondary_market_time_events: Callable[[Any], list[int]]

    def total_asa_funds(self, cfg: utils.DAsaConfig) -> int:
        funding_rate = (
            cfg.interest_rate if cfg.interest_rate else cfg.principal_discount
        )
        return cfg.principal * (sc_cst.BPS + funding_rate) // sc_cst.BPS


def _zero_time_events(current_ts: int) -> utils.TimeEvents:
    primary_open = current_ts + PRIMARY_DISTRIBUTION_DELAY
    primary_close = primary_open + PRIMARY_DISTRIBUTION_DURATION
    issuance_date = primary_close + ISSUANCE_DELAY
    maturity_date = issuance_date + _ZERO_MATURITY_DELAY
    return [primary_open, primary_close, issuance_date, maturity_date]


def _fixed_time_events(current_ts: int) -> utils.TimeEvents:
    primary_open = current_ts + PRIMARY_DISTRIBUTION_DELAY
    primary_close = primary_open + PRIMARY_DISTRIBUTION_DURATION
    issuance_date = primary_close + ISSUANCE_DELAY
    coupon_dates = [
        issuance_date + idx * _FIXED_COUPON_PERIOD
        for idx in range(1, _FIXED_TOTAL_COUPONS + 1)
    ]
    maturity_date = coupon_dates[-1] + MATURITY_DELAY
    return [primary_open, primary_close, issuance_date, *coupon_dates, maturity_date]


def _perpetual_time_events(current_ts: int) -> utils.TimeEvents:
    primary_open = current_ts + PRIMARY_DISTRIBUTION_DELAY
    primary_close = primary_open + PRIMARY_DISTRIBUTION_DURATION
    issuance_date = primary_close + ISSUANCE_DELAY
    return [primary_open, primary_close, issuance_date]


def _zero_config(
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


def _fixed_config(
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
        interest_rate=_FIXED_INTEREST_RATE,
        coupon_rates=_FIXED_COUPON_RATES,
        time_events=time_events,
        time_periods=[],
    )


def _perpetual_config(
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
        time_periods=[(_PERPETUAL_COUPON_PERIOD, 0)],
    )


def _secondary_schedule_with_maturity(state: Any) -> list[int]:
    return [state.issuance_date, state.maturity_date]


def _secondary_schedule_perpetual(state: Any) -> list[int]:
    return [state.issuance_date]


CONTRACT_CASES = (
    ContractCase(
        name="zero_coupon_bond",
        metadata_contract_type=sc_cst.CT_PAM,
        prospectus_url="Zero Coupon Bond Prospectus",
        factory_class=ZeroCouponBondFactory,
        asset_metadata_cls=ZeroAssetMetadata,
        asset_create_args_cls=ZeroAssetCreateArgs,
        asset_config_args_cls=ZeroAssetConfigArgs,
        asset_update_args_cls=ZeroAssetUpdateArgs,
        account_open_args_cls=ZeroAccountOpenArgs,
        primary_distribution_args_cls=ZeroPrimaryDistributionArgs,
        set_secondary_time_events_args_cls=ZeroSetSecondaryTimeEventsArgs,
        rbac_assign_role_args_cls=ZeroRbacAssignRoleArgs,
        rbac_gov_asset_suspension_args_cls=ZeroRbacGovAssetSuspensionArgs,
        set_default_status_args_cls=ZeroSetDefaultStatusArgs,
        capabilities=ContractCapabilities(
            has_maturity=True,
            has_coupon=False,
            has_principal=True,
            has_time_periods=False,
            has_coupon_rates=False,
        ),
        build_time_events=_zero_time_events,
        build_config=_zero_config,
        secondary_market_time_events=_secondary_schedule_with_maturity,
    ),
    ContractCase(
        name="fixed_coupon_bond",
        metadata_contract_type=sc_cst.CT_PAM,
        prospectus_url="Fixed Coupon Bond Prospectus",
        factory_class=FixedCouponBondFactory,
        asset_metadata_cls=FixedAssetMetadata,
        asset_create_args_cls=FixedAssetCreateArgs,
        asset_config_args_cls=FixedAssetConfigArgs,
        asset_update_args_cls=FixedAssetUpdateArgs,
        account_open_args_cls=FixedAccountOpenArgs,
        primary_distribution_args_cls=FixedPrimaryDistributionArgs,
        set_secondary_time_events_args_cls=FixedSetSecondaryTimeEventsArgs,
        rbac_assign_role_args_cls=FixedRbacAssignRoleArgs,
        rbac_gov_asset_suspension_args_cls=FixedRbacGovAssetSuspensionArgs,
        set_default_status_args_cls=FixedSetDefaultStatusArgs,
        capabilities=ContractCapabilities(
            has_maturity=True,
            has_coupon=True,
            has_principal=True,
            has_time_periods=False,
            has_coupon_rates=True,
        ),
        build_time_events=_fixed_time_events,
        build_config=_fixed_config,
        secondary_market_time_events=_secondary_schedule_with_maturity,
    ),
    ContractCase(
        name="perpetual_bond",
        metadata_contract_type=sc_cst.CT_PBN,
        prospectus_url="Perpetual Bond Prospectus",
        factory_class=PerpetualBondFactory,
        asset_metadata_cls=PerpetualAssetMetadata,
        asset_create_args_cls=PerpetualAssetCreateArgs,
        asset_config_args_cls=PerpetualAssetConfigArgs,
        asset_update_args_cls=PerpetualAssetUpdateArgs,
        account_open_args_cls=PerpetualAccountOpenArgs,
        primary_distribution_args_cls=PerpetualPrimaryDistributionArgs,
        set_secondary_time_events_args_cls=PerpetualSetSecondaryTimeEventsArgs,
        rbac_assign_role_args_cls=PerpetualRbacAssignRoleArgs,
        rbac_gov_asset_suspension_args_cls=PerpetualRbacGovAssetSuspensionArgs,
        set_default_status_args_cls=PerpetualSetDefaultStatusArgs,
        capabilities=ContractCapabilities(
            has_maturity=False,
            has_coupon=True,
            has_principal=False,
            has_time_periods=True,
            has_coupon_rates=False,
        ),
        build_time_events=_perpetual_time_events,
        build_config=_perpetual_config,
        secondary_market_time_events=_secondary_schedule_perpetual,
    ),
)
