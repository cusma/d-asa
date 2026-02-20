from typing import Literal, TypeAlias

from algopy import Account, Array, Bytes, FixedBytes, String, Struct, UInt64, arc4

CouponRates: TypeAlias = Array[arc4.UInt16]
TimeEvents: TypeAlias = Array[UInt64]
TimePeriod: TypeAlias = tuple[UInt64, UInt64]
TimePeriods: TypeAlias = Array[TimePeriod]
ProspectusHash: TypeAlias = FixedBytes[Literal[32]]


class AssetInfo(Struct, kw_only=True):
    """D-ASA Info"""

    denomination_asset_id: UInt64
    settlement_asset_id: UInt64
    outstanding_principal: UInt64
    unit_value: UInt64
    day_count_convention: arc4.UInt8
    principal_discount: arc4.UInt16
    interest_rate: arc4.UInt16
    total_supply: UInt64
    circulating_supply: UInt64
    primary_distribution_opening_date: UInt64
    primary_distribution_closure_date: UInt64
    issuance_date: UInt64
    maturity_date: UInt64
    suspended: bool
    performance: arc4.UInt8


# FIXME: Switch to Struct when bytes operations are supported
class AssetMetadata(arc4.Struct, kw_only=True):
    """D-ASA Metadata"""

    contract_type: arc4.UInt8
    calendar: arc4.UInt8
    business_day_convention: arc4.UInt8
    end_of_month_convention: arc4.UInt8
    prepayment_effect: arc4.UInt8
    penalty_type: arc4.UInt8
    prospectus_hash: ProspectusHash
    prospectus_url: String


class AccountInfo(Struct, kw_only=True):
    """D-ASA Account Info"""

    payment_address: Account
    units: UInt64
    unit_value: UInt64
    paid_coupons: UInt64
    suspended: bool


class DayCountFactor(Struct, kw_only=True):
    """D-ASA Day Count Factor"""

    numerator: UInt64
    denominator: UInt64


class CouponsInfo(Struct, kw_only=True):
    """D-ASA Coupons Info"""

    total_coupons: UInt64
    due_coupons: UInt64
    next_coupon_due_date: UInt64
    day_count_factor: DayCountFactor
    all_due_coupons_paid: bool


class PaymentAmounts(Struct, kw_only=True):
    """D-ASA Payment Amounts"""

    interest: UInt64
    principal: UInt64


class PaymentResult(Struct, kw_only=True):
    """D-ASA Payment Result"""

    amount: UInt64
    timestamp: UInt64
    context: Bytes


class SecondaryMarketSchedule(Struct, kw_only=True):
    """D-ASA Secondary Market Schedule"""

    secondary_market_opening_date: UInt64
    secondary_market_closure_date: UInt64


class CurrentUnitsValue(Struct, kw_only=True):
    """D-ASA Account's Current Units Value"""

    units_value: UInt64
    accrued_interest: UInt64
    day_count_factor: DayCountFactor


# FIXME: Switch to Struct when bytes operations are supported
class RoleConfig(arc4.Struct, kw_only=True):
    """D-ASA Role Configuration"""

    role_validity_start: UInt64
    role_validity_end: UInt64
