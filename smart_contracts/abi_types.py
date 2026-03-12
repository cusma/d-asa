from typing import Literal, TypeAlias

from algopy import (
    Account,
    Array,
    Asset,
    BoxMap,
    Bytes,
    FixedBytes,
    String,
    Struct,
    UInt64,
    arc4,
)


class RoleValidity(Struct, kw_only=True):
    """D-ASA Role Configuration"""

    role_validity_start: UInt64
    role_validity_end: UInt64


RbacRole: TypeAlias = BoxMap[Account, RoleValidity]
ContractTypeId: TypeAlias = arc4.UInt8
EventTypeId: TypeAlias = arc4.UInt8
DayCountConvention: TypeAlias = arc4.UInt8
TimeStamp: TypeAlias = UInt64
Hash: TypeAlias = FixedBytes[Literal[32]]


class Prospectus(Struct, kw_only=True):
    """Contract Prospectus."""

    hash: Hash
    url: String


class NormalizedActusTerms(Struct, kw_only=True):
    """Normalized ACTUS terms required by the AVM kernel."""

    contract_type: ContractTypeId
    denomination_asset_id: Asset
    settlement_asset_id: Asset
    total_units: UInt64
    notional_principal: UInt64
    initial_exchange_amount: UInt64
    initial_exchange_date: TimeStamp
    maturity_date: TimeStamp
    secondary_market_opening_date: TimeStamp
    secondary_market_closure_date: TimeStamp
    day_count_convention: DayCountConvention
    rate_reset_spread: UInt64
    rate_reset_multiplier: UInt64
    rate_reset_floor: UInt64
    rate_reset_cap: UInt64
    rate_reset_next: UInt64
    has_rate_reset_floor: bool
    has_rate_reset_cap: bool
    dynamic_principal_redemption: bool
    fixed_point_scale: UInt64


class ExecutionScheduleEntry(Struct, kw_only=True):
    """A single normalized ACTUS event."""

    event_id: UInt64
    event_type: EventTypeId
    scheduled_time: TimeStamp
    accrual_factor: UInt64
    redemption_accrual_factor: UInt64
    next_nominal_interest_rate: UInt64
    next_principal_redemption: UInt64
    next_outstanding_principal: UInt64
    flags: UInt64


ExecutionSchedulePage: TypeAlias = Array[ExecutionScheduleEntry]


class InitialKernelState(Struct, kw_only=True):
    """Initial kernel state at deployment status date."""

    status_date: TimeStamp
    event_cursor: UInt64
    outstanding_principal: UInt64
    interest_calculation_base: UInt64
    nominal_interest_rate: UInt64
    accrued_interest: UInt64
    next_principal_redemption: UInt64
    cumulative_interest_index: UInt64
    cumulative_principal_index: UInt64


class ObservedEventRequest(Struct, kw_only=True):
    """Authorized payload for appending or applying observed ACTUS events."""

    event_id: UInt64
    event_type: EventTypeId
    scheduled_time: TimeStamp
    accrual_factor: UInt64
    redemption_accrual_factor: UInt64
    observed_rate: UInt64
    next_nominal_interest_rate: UInt64
    next_principal_redemption: UInt64
    next_outstanding_principal: UInt64
    flags: UInt64


class KernelState(Struct, kw_only=True):
    """Typed Global State."""

    contract_type: ContractTypeId
    status: UInt64
    total_units: UInt64
    reserved_units_total: UInt64
    initial_exchange_amount: UInt64
    event_cursor: UInt64
    schedule_entry_count: UInt64
    outstanding_principal: UInt64
    interest_calculation_base: UInt64
    nominal_interest_rate: UInt64
    accrued_interest: UInt64
    cumulative_interest_index: UInt64
    cumulative_principal_index: UInt64
    reserved_interest: UInt64
    reserved_principal: UInt64


class AccountPosition(Struct, kw_only=True):
    """
    Tracks the account's units and lazy-settlement state. `interest_checkpoint`
    and `principal_checkpoint` are cumulative per-unit fixed-point indices already
    applied to this account. Any later index growth is converted into absolute
    amounts in `claimable_interest` and `claimable_principal` when the position is
    settled. `settled_cursor` records the global event cursor seen at the last
    settlement.

    Attributes:
        payment_address: Destination for cashflow withdrawals.
        units: Active units that accrue funded cashflows.
        reserved_units: Pre-IED units not yet active.
        suspended: Whether the account is suspended.
        settled_cursor: Global event cursor at the last account settlement.
        interest_checkpoint: Applied cumulative per-unit interest index.
        principal_checkpoint: Applied cumulative per-unit principal index.
        claimable_interest: Absolute interest amount currently claimable.
        claimable_principal: Absolute principal amount currently claimable.
    """

    payment_address: Account
    units: UInt64
    reserved_units: UInt64
    suspended: bool
    settled_cursor: UInt64
    interest_checkpoint: UInt64
    principal_checkpoint: UInt64
    claimable_interest: UInt64
    claimable_principal: UInt64


class CashClaimResult(Struct, kw_only=True):
    """Result returned after a holder cashflow claim attempt."""

    interest_amount: UInt64
    principal_amount: UInt64
    total_amount: UInt64
    timestamp: UInt64
    context: Bytes


class CashFundingResult(Struct, kw_only=True):
    """Result returned after funding one or more due ACTUS cash events."""

    funded_interest: UInt64
    funded_principal: UInt64
    total_funded: UInt64
    processed_events: UInt64
    timestamp: UInt64
