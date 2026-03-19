from __future__ import annotations

from dataclasses import dataclass

from . import enums
from .errors import ActusNormalizationError
from .unix_time import UTCTimeStamp


@dataclass(frozen=True, slots=True)
class NormalizedActusTerms:
    """
    ACTUS normalized contract terms for AVM deployment.

    AVM IDs
    - Contract ID: D-ASA Application ID
    - Contract Type: Contract Type enumerative ID
    - Denomination Asset ID: ASA ID

    AVM Time
    - UTC UNIX timestamp

    AVM Numeric values (UInt64):
    - Amounts: in ASA minimal units
    - Fixed Point are scaled

    NOTE: `notional_unit_value` is an SDK-only metadata. It is used to derive an exact
    `total_units` count before AVM deployment, but it is not persisted on-chain.
    """

    # Contract
    contract_id: int
    contract_type: int

    # Denomination
    denomination_asset_id: int

    # Time
    initial_exchange_date: UTCTimeStamp
    maturity_date: UTCTimeStamp | None
    secondary_market_opening_date: UTCTimeStamp
    secondary_market_closure_date: UTCTimeStamp

    # Principal
    notional_principal: int
    notional_unit_value: int
    initial_exchange_amount: int
    next_principal_redemption_amount: int

    # Interest
    rate_reset_spread: int
    rate_reset_multiplier: int
    rate_reset_floor: int
    rate_reset_cap: int
    rate_reset_next: int

    # Day Count Convention
    day_count_convention: int

    # Scaling
    fixed_point_scale: int

    def __post_init__(self) -> None:
        if self.notional_unit_value <= 0:
            raise ActusNormalizationError("notional_unit_value must be positive")

        if self.notional_principal % self.notional_unit_value != 0:
            raise ActusNormalizationError(
                "D-ASA requires notional_principal be divisible by notional_unit_value"
            )

        if self.secondary_market_opening_date < self.initial_exchange_date:
            raise ActusNormalizationError(
                "secondary_market_opening_date must be at or after initial_exchange_date"
            )

        if self.secondary_market_closure_date <= self.secondary_market_opening_date:
            raise ActusNormalizationError(
                "secondary_market_closure_date must be strictly after secondary_market_opening_date"
            )

    @property
    def total_units(self) -> int:
        return self.notional_principal // self.notional_unit_value

    @property
    def dynamic_principal_redemption(self) -> bool:
        return (
            self.contract_type == enums.CT_ANN
            and not self.next_principal_redemption_amount
        )

    @property
    def has_rate_reset_floor(self) -> bool:
        return self.rate_reset_floor != 0

    @property
    def has_rate_reset_cap(self) -> bool:
        return self.rate_reset_cap != 0


@dataclass(frozen=True, slots=True)
class ExecutionScheduleEntry:
    """Representation of one normalized ACTUS schedule event."""

    event_id: int
    event_type: str
    scheduled_time: UTCTimeStamp
    accrual_factor: int
    redemption_accrual_factor: int
    next_nominal_interest_rate: int
    next_principal_redemption: int
    next_outstanding_principal: int
    flags: int = 0


@dataclass(frozen=True, slots=True)
class InitialKernelState:
    """Contract initial kernel snapshot used for contract configuration."""

    status_date: UTCTimeStamp
    event_cursor: int
    outstanding_principal: int
    interest_calculation_base: int
    nominal_interest_rate: int
    accrued_interest: int
    next_principal_redemption: int
    cumulative_interest_index: int
    cumulative_principal_index: int


@dataclass(frozen=True, slots=True)
class ObservedEventRequest:
    """SDK-side representation of an observed ACTUS event payload."""

    event_type: str
    scheduled_time: UTCTimeStamp
    accrual_factor: int
    redemption_accrual_factor: int
    observed_rate: int
    next_nominal_interest_rate: int
    next_principal_redemption: int
    next_outstanding_principal: int
    flags: int = 0

    def to_schedule_entry(self, event_id: int) -> ExecutionScheduleEntry:
        """Convert an observed payload into the Execution Schedule Entry shape."""
        return ExecutionScheduleEntry(
            event_id=event_id,
            event_type=self.event_type,
            scheduled_time=self.scheduled_time,
            accrual_factor=self.accrual_factor,
            redemption_accrual_factor=self.redemption_accrual_factor,
            next_nominal_interest_rate=self.next_nominal_interest_rate,
            next_principal_redemption=self.next_principal_redemption,
            next_outstanding_principal=self.next_outstanding_principal,
            flags=self.flags,
        )


@dataclass(frozen=True, slots=True)
class ObservedCashEventRequest:
    """SDK-side representation of an observed ACTUS cash-event payload."""

    event_type: str
    scheduled_time: UTCTimeStamp
    accrual_factor: int
    redemption_accrual_factor: int
    next_nominal_interest_rate: int
    next_principal_redemption: int
    next_outstanding_principal: int
    flags: int = 0

    def to_schedule_entry(self, event_id: int) -> ExecutionScheduleEntry:
        """Convert an observed cash payload into the Execution Schedule Entry shape."""
        return ExecutionScheduleEntry(
            event_id=event_id,
            event_type=self.event_type,
            scheduled_time=self.scheduled_time,
            accrual_factor=self.accrual_factor,
            redemption_accrual_factor=self.redemption_accrual_factor,
            next_nominal_interest_rate=self.next_nominal_interest_rate,
            next_principal_redemption=self.next_principal_redemption,
            next_outstanding_principal=self.next_outstanding_principal,
            flags=self.flags,
        )


@dataclass(frozen=True, slots=True)
class AccountPosition:
    """SDK-side D-ASA Contract holder position."""

    units: int
    reserved_units: int
    payment_address: str
    suspended: bool
    settled_cursor: int
    interest_checkpoint: int
    principal_checkpoint: int
    claimable_interest: int
    claimable_principal: int


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Bundle returned by normalization for AVM deployment and verification."""

    terms: NormalizedActusTerms
    schedule: tuple[ExecutionScheduleEntry, ...]
    initial_state: InitialKernelState

    def schedule_pages(
        self, page_size: int
    ) -> tuple[tuple[ExecutionScheduleEntry, ...], ...]:
        """Chunk the normalized schedule into fixed-size upload pages."""
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        pages: list[tuple[ExecutionScheduleEntry, ...]] = []
        for start in range(0, len(self.schedule), page_size):
            pages.append(self.schedule[start : start + page_size])
        return tuple(pages)
