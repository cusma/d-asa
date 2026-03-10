from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionTerms:
    """Non-ACTUS contract execution terms."""

    unit_value: int
    total_units: int
    fixed_point_scale: int
    secondary_market_opening_date: int | None
    secondary_market_closure_date: int | None


@dataclass(frozen=True, slots=True)
class NormalizedActusTerms(ExecutionTerms):
    """
    ACTUS normalized contract terms for AVM deployment.

    NOTE: `unit_value` is an SDK-only metadata. It is used to derive an exact
    `total_units` count before AVM deployment, but it is not persisted on-chain.
    """

    contract_id: str
    denomination_asset_id: int
    settlement_asset_id: int
    notional_principal: int
    initial_exchange_amount: int
    initial_exchange_date: int
    maturity_date: int | None
    day_count_convention: int
    rate_reset_spread: int
    rate_reset_multiplier: int
    rate_reset_floor: int
    rate_reset_cap: int
    rate_reset_next: int
    has_rate_reset_floor: bool
    has_rate_reset_cap: bool
    dynamic_principal_redemption: bool


@dataclass(frozen=True, slots=True)
class ExecutionScheduleEntry:
    """Representation of one normalized ACTUS schedule event."""

    event_id: int
    event_type: str
    scheduled_time: int
    accrual_factor: int
    redemption_accrual_factor: int
    next_nominal_interest_rate: int
    next_principal_redemption: int
    next_outstanding_principal: int
    flags: int = 0


@dataclass(frozen=True, slots=True)
class InitialKernelState:
    """Contract initial kernel snapshot used for contract configuration."""

    status_date: int
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
    scheduled_time: int
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
