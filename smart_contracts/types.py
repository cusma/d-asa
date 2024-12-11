from typing import TypeAlias

from algopy import arc4

AssetMetadata: TypeAlias = arc4.DynamicBytes
CouponRates: TypeAlias = arc4.DynamicArray[arc4.UInt16]
TimeEvents: TypeAlias = arc4.DynamicArray[arc4.UInt64]
TimePeriods: TypeAlias = arc4.DynamicArray[arc4.Tuple[arc4.UInt64, arc4.UInt64]]


class AssetInfo(arc4.Struct, kw_only=True):
    """D-ASA Info"""

    denomination_asset_id: arc4.UInt64
    outstanding_principal: arc4.UInt64
    unit_value: arc4.UInt64
    day_count_convention: arc4.UInt8
    interest_rate: arc4.UInt16
    total_supply: arc4.UInt64
    circulating_supply: arc4.UInt64
    primary_distribution_opening_date: arc4.UInt64
    primary_distribution_closure_date: arc4.UInt64
    issuance_date: arc4.UInt64
    maturity_date: arc4.UInt64
    suspended: arc4.Bool
    defaulted: arc4.Bool


class AccountInfo(arc4.Struct, kw_only=True):
    """D-ASA Account Info"""

    payment_address: arc4.Address
    units: arc4.UInt64
    unit_value: arc4.UInt64
    paid_coupons: arc4.UInt64
    suspended: arc4.Bool


class DayCountFactor(arc4.Struct, kw_only=True):
    """D-ASA Day Count Factor"""

    numerator: arc4.UInt64
    denominator: arc4.UInt64


class CouponsInfo(arc4.Struct, kw_only=True):
    """D-ASA Coupons Info"""

    total_coupons: arc4.UInt64
    due_coupons: arc4.UInt64
    next_coupon_due_date: arc4.UInt64
    day_count_factor: DayCountFactor
    all_due_coupons_paid: arc4.Bool


class PaymentAmounts(arc4.Struct, kw_only=True):
    """D-ASA Payment Amounts"""

    interest: arc4.UInt64
    principal: arc4.UInt64


class PaymentResult(arc4.Struct, kw_only=True):
    """D-ASA Payment Result"""

    amount: arc4.UInt64
    timestamp: arc4.UInt64
    context: arc4.DynamicBytes


class SecondaryMarketSchedule(arc4.Struct, kw_only=True):
    """D-ASA Secondary Market Schedule"""

    secondary_market_opening_date: arc4.UInt64
    secondary_market_closure_date: arc4.UInt64


class CurrentUnitsValue(arc4.Struct, kw_only=True):
    """D-ASA Account's Current Units Value"""

    units_value: arc4.UInt64
    accrued_interest: arc4.UInt64
    day_count_factor: DayCountFactor


class RoleConfig(arc4.Struct, kw_only=True):
    """D-ASA Role Configuration"""

    role_validity_start: arc4.UInt64
    role_validity_end: arc4.UInt64
