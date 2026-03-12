"""
ACTUS Kernel

This module contains the contract-type-independent part of the execution engine.
It validates normalized terms, classifies schedule entries, computes cashflow
magnitudes, advances the contract state machine, and exposes the generic ABI methods
shared by the D-ASA variants.

Glossary used in this file:
- `IED`: initial exchange date. The contract moves from configured to active.
- `IP`: interest payment.
- `PR`: principal redemption.
- `PI`: principal increase or capitalization.
- `MD`: maturity.
- `RR` / `RRF`: rate reset from an observed rate or a pre-fixed rate.
- `IPCB`: interest calculation base reset.
- `PRF`: principal redemption fixing for dynamic annuities.

The schedule is normalized off chain before it reaches the AVM. Each entry
therefore already carries the next contractual state, and the kernel mostly
needs to verify that the next entry is due, derive any payable amount, then
move on-chain state to the entry's `next_*` values.
"""

from algopy import (
    Account,
    Asset,
    BoxMap,
    Bytes,
    Global,
    String,
    UInt64,
    arc4,
    ensure_budget,
    itxn,
    op,
)

from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import enums
from smart_contracts import errors as err
from smart_contracts.events import ExecutionEvent

from .rbac import RbacModule


class ActusKernelModule(RbacModule):
    """
    Implement the ACTUS schedule and state transitions.
    """

    def __init__(self) -> None:
        super().__init__()

        # Contract
        self.status = UInt64(enums.STATUS_INACTIVE)
        self.contract_type = UInt64()

        # Prospectus (Informational)
        self.prospectus_hash = Bytes()
        self.prospectus_url = String()

        # Denomination
        self.denomination_asset_id = Asset()
        self.settlement_asset_id = Asset()

        # Time
        self.initial_exchange_date = typ.TimeStamp()
        self.maturity_date = typ.TimeStamp()
        self.transfer_opening_date = typ.TimeStamp()
        self.transfer_closure_date = typ.TimeStamp()

        # Day Count Convention
        self.day_count_convention = UInt64()

        # Units
        self.total_units = UInt64()
        self.reserved_units_total = UInt64()

        # Principal
        self.initial_exchange_amount = UInt64()
        self.outstanding_principal = UInt64()
        self.next_principal_redemption = UInt64()
        self.dynamic_principal_redemption = False

        # Interest
        self.interest_calculation_base = UInt64()
        self.accrued_interest = UInt64()

        # Interest Rates
        self.nominal_interest_rate = UInt64()
        self.rate_reset_spread = UInt64()
        self.rate_reset_multiplier = UInt64()
        self.rate_reset_floor = UInt64()
        self.rate_reset_cap = UInt64()
        self.rate_reset_next = UInt64()
        self.has_rate_reset_floor = False
        self.has_rate_reset_cap = False

        # Primary Distribution
        self.reserved_principal = UInt64()
        self.reserved_interest = UInt64()

        # Cumulative Per-Unit Fixed-Point Indexes
        self.cumulative_interest_index = UInt64()
        self.cumulative_principal_index = UInt64()

        # Schedule
        self.schedule_page = BoxMap(
            UInt64,
            typ.ExecutionSchedulePage,
            key_prefix=cst.PREFIX_ID_SCHEDULE_PAGE,
        )
        self.event_cursor = UInt64()
        self.schedule_entry_count = UInt64()

        # Scaling
        self.fixed_point_scale = UInt64()

    ############################################################################
    # AVM-specific Contract State
    ############################################################################

    def _status_is_inactive(self) -> bool:
        """Return whether the contract is inactive."""
        return self.status == UInt64(enums.STATUS_INACTIVE)

    def _status_is_active(self) -> bool:
        """Return whether the contract is active after IED."""
        return self.status == UInt64(enums.STATUS_ACTIVE)

    def _status_is_pending_ied(self) -> bool:
        """Return whether the contract is configured but still awaiting IED."""
        return self.status == UInt64(enums.STATUS_PENDING_IED)

    def _status_is_ended(self) -> bool:
        """Return whether the contract has reached its terminal state."""
        return self.status == UInt64(enums.STATUS_ENDED)

    def _assert_configured(self) -> None:
        """Require the contract to have completed configuration."""
        assert self.status != UInt64(enums.STATUS_INACTIVE), err.NOT_CONFIGURED

    def _assert_initial_exchange_executed(self) -> None:
        """Require the initial exchange event to have been executed."""
        assert not self._status_is_pending_ied(), err.PENDING_IED

    ############################################################################
    # Math and Conversions
    ############################################################################

    def _scaled_mul_div(
        self, multiplicand: UInt64, multiplier: UInt64, divisor: UInt64
    ) -> UInt64:
        """Multiply and divide in fixed-point space using wide AVM math."""
        if multiplicand == UInt64(0) or multiplier == UInt64(0):
            return UInt64(0)
        high, low = op.mulw(multiplicand, multiplier)
        return op.divw(high, low, divisor)

    def _amount_to_index_delta(self, amount: UInt64) -> UInt64:
        """Convert a contract-wide amount into a per-unit cumulative index delta."""
        if amount == UInt64(0):
            return UInt64(0)
        assert self.total_units > UInt64(0), err.NO_UNITS
        return self._scaled_mul_div(amount, self.fixed_point_scale, self.total_units)

    def _index_delta_to_amount(self, index_delta: UInt64) -> UInt64:
        """
        Convert a per-unit index delta back into a contract-wide amount.

        This mirrors `_amount_to_index_delta()` and keeps funding amounts aligned
        with what holders can later realize from the cumulative indices.
        """
        if index_delta == UInt64(0):
            return UInt64(0)
        return self._scaled_mul_div(
            self.total_units,
            index_delta,
            self.fixed_point_scale,
        )

    ############################################################################
    # Schedule
    ############################################################################

    def _schedule_page_index(self, event_id: UInt64) -> UInt64:
        """Return the schedule page index containing the given event id."""
        return event_id // UInt64(cst.SCHEDULE_PAGE_SIZE)

    def _schedule_page_offset(self, event_id: UInt64) -> UInt64:
        """Return the offset of an event within its schedule page."""
        return event_id % UInt64(cst.SCHEDULE_PAGE_SIZE)

    def _store_schedule_page(
        self, page_index: UInt64, schedule_page: typ.ExecutionSchedulePage
    ) -> None:
        """Persist a normalized schedule page."""
        self.schedule_page[page_index] = schedule_page.copy()

    def _get_schedule_entry(self, event_id: UInt64) -> typ.ExecutionScheduleEntry:
        """Load a normalized schedule entry by global event id."""
        assert event_id < self.schedule_entry_count, err.INVALID_EVENT_ID
        page_index = self._schedule_page_index(event_id)
        assert page_index in self.schedule_page, err.INVALID_SCHEDULE_PAGE
        page = self.schedule_page[page_index].copy()
        offset = self._schedule_page_offset(event_id)
        assert offset < page.length, err.INVALID_SCHEDULE_PAGE
        return page[offset].copy()

    ############################################################################
    # ACTUS Composition Validation
    ############################################################################

    def _is_supported_contract_type(self, contract_type: UInt64) -> bool:
        """Return whether the contract type belongs to the supported ACTUS types."""
        return contract_type in (
            UInt64(enums.CT_PAM),
            UInt64(enums.CT_ANN),
            UInt64(enums.CT_NAM),
            UInt64(enums.CT_LAM),
            UInt64(enums.CT_LAX),
            UInt64(enums.CT_CLM),
        )

    def _assert_supported_contract_type(self, contract_type: UInt64) -> None:
        """Require the configured contract type to be supported by the kernel."""
        assert self._is_supported_contract_type(contract_type), err.INVALID_ACTUS_CONFIG

    def _supports_observed_events(self) -> bool:
        """Return whether the configured type may append observed events."""
        return self.contract_type == UInt64(enums.CT_CLM)

    def _event_allowed_for_contract_type(
        self, contract_type: UInt64, event_type: UInt64
    ) -> bool:
        """
        Return whether `event_type` may appear in the normalized schedule.

        This is the kernel's compatibility matrix between contract families and
        schedule events. It does not say whether the event is due now, only
        whether it is a valid event kind for the chosen ACTUS contract type.
        """
        # Common events supported by all contract types
        common_events = (
            UInt64(enums.EVT_IED),
            UInt64(enums.EVT_IP),
            UInt64(enums.EVT_MD),
            UInt64(enums.EVT_RR),
            UInt64(enums.EVT_RRF),
        )

        # Check common events first
        if event_type in common_events:
            return True

        # Contract-specific additional events
        if contract_type == UInt64(enums.CT_PAM):
            # PAM only supports common events
            return False

        if contract_type == UInt64(enums.CT_LAM) or contract_type == UInt64(
            enums.CT_NAM
        ):
            # LAM/NAM add: PR, IPCB
            return event_type in (
                UInt64(enums.EVT_PR),
                UInt64(enums.EVT_IPCB),
            )

        if contract_type == UInt64(enums.CT_ANN):
            # ANN adds: PR, IPCB, PRF
            return event_type in (
                UInt64(enums.EVT_PR),
                UInt64(enums.EVT_IPCB),
                UInt64(enums.EVT_PRF),
            )

        if contract_type == UInt64(enums.CT_LAX):
            # LAX adds: PR, PI, IPCB, PRF
            return event_type in (
                UInt64(enums.EVT_PR),
                UInt64(enums.EVT_PI),
                UInt64(enums.EVT_IPCB),
                UInt64(enums.EVT_PRF),
            )

        if contract_type == UInt64(enums.CT_CLM):
            # CLM adds: PR
            return event_type == UInt64(enums.EVT_PR)

        return False

    def _is_supported_day_count_convention(self, day_count_convention: UInt64) -> bool:
        """Return whether the normalized day-count identifier is accepted in v1."""
        return day_count_convention in (
            UInt64(enums.DCC_AA),
            UInt64(enums.DCC_A360),
            UInt64(enums.DCC_A365),
            UInt64(enums.DCC_30E360ISDA),
            UInt64(enums.DCC_30E360),
        )

    def _assert_supported_day_count_convention(
        self, day_count_convention: UInt64
    ) -> None:
        """Require the normalized day-count identifier to be one the AVM accepts."""
        assert self._is_supported_day_count_convention(
            day_count_convention
        ), err.INVALID_DAY_COUNT_CONVENTION

    def _assert_event_allowed_for_contract_type(
        self, contract_type: UInt64, event_type: UInt64
    ) -> None:
        """Require a schedule event to be compatible with the stored contract type."""
        assert self._event_allowed_for_contract_type(
            contract_type, event_type
        ), err.INVALID_ACTUS_CONFIG

    def _validate_terms_for_contract_type(
        self, contract_type: UInt64, terms: typ.NormalizedActusTerms
    ) -> None:
        """Validate normalized terms that depend on the selected contract type."""
        assert terms.initial_exchange_amount > UInt64(0), err.INVALID_ACTUS_CONFIG
        self._assert_supported_day_count_convention(
            terms.day_count_convention.as_uint64()
        )
        if contract_type != UInt64(enums.CT_ANN):
            assert not terms.dynamic_principal_redemption, err.INVALID_ACTUS_CONFIG

    def _is_dynamic_annuity(self) -> bool:
        """Return whether the current contract uses ANN dynamic redemption."""
        return (
            self.contract_type == UInt64(enums.CT_ANN)
            and self.dynamic_principal_redemption
        )

    ############################################################################
    # Event Classifiers
    ############################################################################

    def _event_is_cash(self, event_type: UInt64) -> bool:
        """
        Return whether the event reserves settlement funds for holders.

        Cash events increase the global per-unit indices and ring-fence funds in
        `reserved_interest` / `reserved_principal` for later holder claims.
        """
        return event_type in (
            UInt64(enums.EVT_IP),
            UInt64(enums.EVT_PR),
            UInt64(enums.EVT_MD),
        )

    def _event_is_non_cash(self, event_type: UInt64) -> bool:
        """
        Return whether the event only mutates contract state.

        Non-cash events still advance the schedule cursor, but they do not
        reserve settlement assets in the holder claim ledger.
        """
        return event_type in (
            UInt64(enums.EVT_IED),
            UInt64(enums.EVT_PI),
            UInt64(enums.EVT_RR),
            UInt64(enums.EVT_RRF),
            UInt64(enums.EVT_IPCB),
            UInt64(enums.EVT_PRF),
        )

    def _event_is_rate_reset(self, event_type: UInt64) -> bool:
        """Return whether the event updates the current contractual interest rate."""
        return event_type in (UInt64(enums.EVT_RR), UInt64(enums.EVT_RRF))

    ############################################################################
    # Amounts Computation
    ############################################################################

    def _entry_interest_segment(self, entry: typ.ExecutionScheduleEntry) -> UInt64:
        """
        Compute the interest accrued since the previous status date.

        The schedule already provides the accrual factor for the period. The
        kernel multiplies that factor by the current interest base and nominal
        rate to get the incremental carry attributable to this entry.
        """
        if (
            entry.accrual_factor == UInt64(0)
            or self.nominal_interest_rate == UInt64(0)
            or self.interest_calculation_base == UInt64(0)
        ):
            return UInt64(0)
        accrued = self._scaled_mul_div(
            self.interest_calculation_base,
            self.nominal_interest_rate,
            self.fixed_point_scale,
        )
        return self._scaled_mul_div(
            accrued,
            entry.accrual_factor,
            self.fixed_point_scale,
        )

    def _entry_interest_amount(self, entry: typ.ExecutionScheduleEntry) -> UInt64:
        """
        Return the contractual interest due for a cash event.

        `IP` and `MD` settle all currently accrued carry plus the period segment
        produced by this entry. `PR` does not settle interest separately here.
        """
        event_type = entry.event_type.as_uint64()
        if event_type not in (UInt64(enums.EVT_IP), UInt64(enums.EVT_MD)):
            return UInt64(0)
        return self.accrued_interest + self._entry_interest_segment(entry)

    def _entry_principal_amount(self, entry: typ.ExecutionScheduleEntry) -> UInt64:
        """
        Return the contractual principal due for a cash event.

        For standard schedules the entry directly tells the kernel the next
        outstanding principal. Dynamic annuities are different: the scheduled
        redemption is treated as a total payment target, so principal is the
        residual left after interest is covered.
        """
        event_type = entry.event_type.as_uint64()
        if event_type not in (UInt64(enums.EVT_PR), UInt64(enums.EVT_MD)):
            return UInt64(0)
        if self._is_dynamic_annuity():
            if event_type == UInt64(enums.EVT_MD):
                return self.outstanding_principal
            interest_due = self.accrued_interest + self._entry_interest_segment(entry)
            if self.next_principal_redemption <= interest_due:
                return UInt64(0)
            principal_amount = self.next_principal_redemption - interest_due
            if principal_amount > self.outstanding_principal:
                return self.outstanding_principal
            return principal_amount
        assert (
            entry.next_outstanding_principal <= self.outstanding_principal
        ), err.INVALID_ACTUS_CONFIG
        return self.outstanding_principal - entry.next_outstanding_principal

    def _entry_ied_amount(self, entry: typ.ExecutionScheduleEntry) -> UInt64:
        """
        Return the contractual IED amount stored in normalized terms.

        `IED` is a lifecycle transition on chain, not a funded holder cashflow,
        so the amount is emitted for traceability but not settled from escrow.
        """
        assert entry.event_type.as_uint64() == UInt64(enums.EVT_IED), err.NOT_EVT_IED
        return self.initial_exchange_amount

    def _reserved_total(self) -> UInt64:
        """Return the settlement funds already ring-fenced for holders."""
        return self.reserved_interest + self.reserved_principal

    ############################################################################
    # Annuity (ANN) Specific Logic
    ############################################################################

    def _discount_annuity_factor(
        self,
        discount_factor: UInt64,
        redemption_factor: UInt64,
    ) -> UInt64:
        """Advance an annuity discount factor by one redemption period."""
        if redemption_factor == UInt64(0):
            return discount_factor
        period_rate = self.fixed_point_scale + self._scaled_mul_div(
            self.nominal_interest_rate,
            redemption_factor,
            self.fixed_point_scale,
        )
        assert period_rate > UInt64(0), err.INVALID_ACTUS_CONFIG
        return self._scaled_mul_div(
            discount_factor,
            self.fixed_point_scale,
            period_rate,
        )

    def _recalculate_annuity_payment(self, entry: typ.ExecutionScheduleEntry) -> UInt64:
        """
        Recompute the next annuity payment after a `PRF` event.

        The method walks the remaining redemption-bearing schedule entries,
        discounts each future payment bucket, and solves for the flat payment
        that amortizes the current outstanding state.
        """
        discount_factor = self.fixed_point_scale
        denominator = UInt64(0)
        skip_first_redemption = False

        if entry.redemption_accrual_factor > UInt64(0):
            # An initial PRF may describe the first redemption period directly.
            discount_factor = self._discount_annuity_factor(
                discount_factor,
                entry.redemption_accrual_factor,
            )
            denominator += discount_factor
            skip_first_redemption = True

        future_event_id = self.event_cursor + UInt64(1)
        while future_event_id < self.schedule_entry_count:
            future_entry = self._get_schedule_entry(future_event_id)
            future_event_type = future_entry.event_type.as_uint64()
            # Only redemption-bearing events contribute to the annuity denominator.
            is_redemption_event = future_event_type == UInt64(enums.EVT_PR) or (
                future_event_type == UInt64(enums.EVT_MD)
                and future_entry.redemption_accrual_factor > UInt64(0)
            )
            if is_redemption_event:
                if skip_first_redemption:
                    skip_first_redemption = False
                else:
                    discount_factor = self._discount_annuity_factor(
                        discount_factor,
                        future_entry.redemption_accrual_factor,
                    )
                    denominator += discount_factor
            future_event_id += UInt64(1)

        assert denominator > UInt64(0), err.INVALID_ACTUS_CONFIG
        numerator = self.outstanding_principal
        if entry.flags & UInt64(enums.FLAG_INITIAL_PRF) == UInt64(0):
            # Subsequent PRF events amortize both principal and already accrued carry.
            numerator += self.accrued_interest
        return self._scaled_mul_div(
            numerator,
            self.fixed_point_scale,
            denominator,
        )

    ############################################################################
    # Apply Schedule Entries
    ############################################################################

    def _apply_cash_entry(
        self, entry: typ.ExecutionScheduleEntry
    ) -> tuple[UInt64, UInt64]:
        """
        Apply one due cash event and reserve its amount for later claims.

        The kernel derives the contract-wide interest and principal due, turns
        those amounts into per-unit index deltas, reserves settlement funds, and
        advances the global cursor to the next schedule entry.
        """
        assert entry.event_id == self.event_cursor, err.INVALID_EVENT_CURSOR
        assert entry.scheduled_time <= Global.latest_timestamp, err.NO_DUE_CASHFLOW

        interest_amount_due = self._entry_interest_amount(entry)
        principal_amount_due = self._entry_principal_amount(entry)
        next_outstanding_principal = entry.next_outstanding_principal
        next_interest_base = entry.next_outstanding_principal

        if self._is_dynamic_annuity():
            event_type = entry.event_type.as_uint64()
            # Dynamic annuities derive next state from the payment decomposition,
            # not only from the precomputed `next_*` fields.
            if event_type == UInt64(enums.EVT_PR):
                next_outstanding_principal = (
                    self.outstanding_principal - principal_amount_due
                )
                next_interest_base = next_outstanding_principal
            elif event_type == UInt64(enums.EVT_IP):
                next_outstanding_principal = self.outstanding_principal
                next_interest_base = self.interest_calculation_base
            elif event_type == UInt64(enums.EVT_MD):
                next_outstanding_principal = UInt64(0)
                next_interest_base = UInt64(0)

        # Funding uses per-unit cumulative indices so each holder can settle
        # independently from its current unit balance.
        interest_index_delta = self._amount_to_index_delta(interest_amount_due)
        principal_index_delta = self._amount_to_index_delta(principal_amount_due)
        interest_amount = self._index_delta_to_amount(interest_index_delta)
        principal_amount = self._index_delta_to_amount(principal_index_delta)
        required_amount = interest_amount + principal_amount
        assert (
            self._available_settlement_funds() >= required_amount
        ), err.NOT_ENOUGH_FUNDS

        self.reserved_interest += interest_amount
        self.reserved_principal += principal_amount
        self.cumulative_interest_index += interest_index_delta
        self.cumulative_principal_index += principal_index_delta
        if entry.event_type.as_uint64() == UInt64(enums.EVT_PR):
            # For PR, the period interest stays accrued until a later IP or MD.
            self.accrued_interest += self._entry_interest_segment(entry)
        else:
            self.accrued_interest = UInt64(0)
        if not self._is_dynamic_annuity() or entry.event_type.as_uint64() == UInt64(
            enums.EVT_MD
        ):
            self.next_principal_redemption = entry.next_principal_redemption
        self.outstanding_principal = next_outstanding_principal
        self.interest_calculation_base = next_interest_base
        self.event_cursor += UInt64(1)

        if entry.event_type == arc4.UInt8(
            enums.EVT_MD
        ) and self.outstanding_principal == UInt64(0):
            self.status = UInt64(enums.STATUS_ENDED)
            self.interest_calculation_base = UInt64(0)

        self._emit_execution_event(
            entry=entry,
            payoff=interest_amount + principal_amount,
            settled_amount=interest_amount + principal_amount,
        )
        return interest_amount, principal_amount

    def _apply_non_cash_schedule_entry(
        self, entry: typ.ExecutionScheduleEntry, payload: typ.ObservedEventRequest
    ) -> None:
        """
        Apply one due non-cash event and advance the kernel state.

        Non-cash events do not reserve settlement assets, but they can activate
        issuance, capitalize principal, change the running rate, or recalculate
        future annuity payments.
        """
        assert entry.event_id == self.event_cursor, err.INVALID_EVENT_CURSOR
        assert entry.scheduled_time <= Global.latest_timestamp, err.NO_DUE_CASHFLOW

        event_type = entry.event_type.as_uint64()
        if event_type == UInt64(enums.EVT_IED):
            # IED finalizes issuance: reserved units become activatable and the
            # schedule's initial contractual state becomes live.
            assert self._status_is_pending_ied(), err.INVALID_ACTUS_CONFIG
            assert (
                self.reserved_units_total == self.total_units
            ), err.PRIMARY_DISTRIBUTION_INCOMPLETE
            self.outstanding_principal = entry.next_outstanding_principal
            self.interest_calculation_base = entry.next_outstanding_principal
            self.nominal_interest_rate = entry.next_nominal_interest_rate
            self.accrued_interest = UInt64(0)
            self.next_principal_redemption = entry.next_principal_redemption
            self.event_cursor += UInt64(1)
            self.status = UInt64(enums.STATUS_ACTIVE)
            self._emit_execution_event(
                entry=entry,
                payoff=self._entry_ied_amount(entry),
                settled_amount=UInt64(0),
            )
            return

        self._assert_initial_exchange_executed()
        self.accrued_interest += self._entry_interest_segment(entry)

        if event_type == UInt64(enums.EVT_RR):
            # RR derives the next rate from an observed oracle value plus the
            # contract spread / multiplier terms, then enforces floor and cap.
            observed_rate = self._scaled_mul_div(
                payload.observed_rate,
                self.rate_reset_multiplier,
                self.fixed_point_scale,
            )
            self.nominal_interest_rate = self._clamp_rate(
                observed_rate + self.rate_reset_spread
            )
        elif event_type == UInt64(enums.EVT_RRF):
            next_rate = entry.next_nominal_interest_rate
            if next_rate == UInt64(0):
                next_rate = self.rate_reset_next
            self.nominal_interest_rate = next_rate
        else:
            if entry.next_nominal_interest_rate != UInt64(0):
                self.nominal_interest_rate = entry.next_nominal_interest_rate

        if event_type == UInt64(enums.EVT_PI):
            self.outstanding_principal = entry.next_outstanding_principal
            self.interest_calculation_base = entry.next_outstanding_principal
        elif event_type == UInt64(enums.EVT_IPCB):
            # IPCB keeps principal unchanged and only resets the interest base.
            self.interest_calculation_base = self.outstanding_principal

        if self._is_dynamic_annuity():
            if event_type == UInt64(enums.EVT_PRF):
                ensure_budget(
                    required_budget=(
                        UInt64(cst.OP_UP_NON_CASH_BASE_BUDGET)
                        + (
                            self.schedule_entry_count - self.event_cursor
                        )
                        * UInt64(cst.OP_UP_NON_CASH_PER_ENTRY_BUDGET)
                    ),
                )
                self.next_principal_redemption = self._recalculate_annuity_payment(
                    entry
                )
        else:
            self.next_principal_redemption = entry.next_principal_redemption
        self.event_cursor += UInt64(1)
        self._emit_execution_event(
            entry=entry,
            payoff=UInt64(0),
            settled_amount=UInt64(0),
        )

    ############################################################################
    # Execution Events
    ############################################################################

    def _emit_execution_event(
        self,
        *,
        entry: typ.ExecutionScheduleEntry,
        payoff: UInt64,
        settled_amount: UInt64,
    ) -> None:
        """Emit a non-normative ARC-28 receipt for one applied schedule entry."""
        arc4.emit(
            ExecutionEvent(
                contract_id=Global.current_application_id.id,
                event_id=entry.event_id,
                event_type=entry.event_type,
                scheduled_time=entry.scheduled_time,
                applied_at=Global.latest_timestamp,
                payoff=payoff,
                payoff_sign=arc4.UInt8(
                    self._payoff_sign(entry.event_type.as_uint64(), payoff)
                ),
                settled_amount=settled_amount,
                currency_id=self.settlement_asset_id,
                sequence=entry.event_id + UInt64(1),
            )
        )

    ############################################################################
    # Others
    ############################################################################

    def _available_settlement_funds(self) -> UInt64:
        """Return the app's free settlement balance after reserved cashflows."""
        balance = self.settlement_asset_id.balance(Global.current_application_address)
        reserved_total = self._reserved_total()
        assert balance >= reserved_total, err.NOT_ENOUGH_FUNDS
        return balance - reserved_total

    def _clamp_rate(self, rate: UInt64) -> UInt64:
        """Apply optional floor and cap terms to a normalized rate."""
        if self.has_rate_reset_floor and rate < self.rate_reset_floor:
            rate = self.rate_reset_floor
        if self.has_rate_reset_cap and rate > self.rate_reset_cap:
            rate = self.rate_reset_cap
        return rate

    def _payoff_sign(self, event_type: UInt64, payoff: UInt64) -> UInt64:
        """Resolve the contractual payoff sign from cashflow direction alone."""
        if payoff == UInt64(0):
            return UInt64(enums.PAYOFF_SIGN_POSITIVE)
        if event_type in (UInt64(enums.EVT_IED), UInt64(enums.EVT_PI)):
            return UInt64(enums.PAYOFF_SIGN_POSITIVE)
        return UInt64(enums.PAYOFF_SIGN_NEGATIVE)

    def _assert_no_due_event_pending(self) -> None:
        """
        Require there to be no due schedule entry at the current cursor.

        Transfers settle holders against the current global indices. Allowing a
        transfer while a due event is still unapplied would let positions move
        before the shared contract state catches up.
        """
        if self.event_cursor >= self.schedule_entry_count:
            return
        next_entry = self._get_schedule_entry(self.event_cursor)
        assert (
            next_entry.scheduled_time > Global.latest_timestamp
        ), err.PENDING_ACTUS_EVENT

    ############################################################################
    # Contract Configuration
    ############################################################################

    def _assert_denomination_asset(self, denomination_asset_id: Asset) -> None:
        # The reference implementation has on-chain denomination with ASA
        _creator, exists = op.AssetParamsGet.asset_creator(denomination_asset_id)
        assert exists, err.INVALID_DENOMINATION

    def _set_denomination_asset(self, denomination_asset_id: Asset) -> None:
        self.denomination_asset_id = denomination_asset_id

    def _assert_settlement_asset(self, settlement_asset_id: Asset) -> None:
        # The reference implementation settlement asset is the denomination asset
        assert (
            settlement_asset_id == self.denomination_asset_id
        ), err.INVALID_SETTLEMENT_ASSET

    def _set_settlement_asset(self, settlement_asset_id: Asset) -> None:
        self.settlement_asset_id = settlement_asset_id
        # The reference implementation has on-chain settlement with ASA
        itxn.AssetTransfer(
            xfer_asset=self.settlement_asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=Global.min_txn_fee,
        ).submit()

    def _store_contract_config(
        self,
        contract_type: UInt64,
        terms: typ.NormalizedActusTerms,
        initial_state: typ.InitialKernelState,
    ) -> None:
        """Persist normalized terms and initial kernel state once."""

        self._validate_terms_for_contract_type(contract_type, terms)
        assert self.status == UInt64(enums.STATUS_INACTIVE), err.ALREADY_CONFIGURED
        assert self.initial_exchange_amount == UInt64(0), err.ALREADY_CONFIGURED

        # Set Denomination Asset
        self._assert_denomination_asset(terms.denomination_asset_id)
        self._set_denomination_asset(terms.denomination_asset_id)

        # Set Settlement Asset
        self._assert_settlement_asset(terms.settlement_asset_id)
        self._set_settlement_asset(terms.settlement_asset_id)

        # Units
        self.total_units = terms.total_units
        self.reserved_units_total = UInt64(0)

        # Day-Count Conventions
        self.day_count_convention = terms.day_count_convention.as_uint64()

        # Time
        self.initial_exchange_date = terms.initial_exchange_date
        self.maturity_date = terms.maturity_date
        self.next_principal_redemption = initial_state.next_principal_redemption

        # Principal
        self.initial_exchange_amount = terms.initial_exchange_amount
        self.dynamic_principal_redemption = terms.dynamic_principal_redemption
        self.outstanding_principal = initial_state.outstanding_principal

        # Interest
        self.accrued_interest = initial_state.accrued_interest

        # Interest Rate
        self.nominal_interest_rate = initial_state.nominal_interest_rate
        self.interest_calculation_base = initial_state.interest_calculation_base
        self.rate_reset_spread = terms.rate_reset_spread
        self.rate_reset_multiplier = terms.rate_reset_multiplier
        self.rate_reset_floor = terms.rate_reset_floor
        self.rate_reset_cap = terms.rate_reset_cap
        self.rate_reset_next = terms.rate_reset_next
        self.has_rate_reset_floor = terms.has_rate_reset_floor
        self.has_rate_reset_cap = terms.has_rate_reset_cap

        # Scaling
        self.fixed_point_scale = terms.fixed_point_scale

        # Schedule Processing
        self.event_cursor = initial_state.event_cursor

        # Per-Unit Fixed-Point Indexes
        self.cumulative_interest_index = initial_state.cumulative_interest_index
        self.cumulative_principal_index = initial_state.cumulative_principal_index

        # Reserved Amount (for executed cashflows)
        self.reserved_interest = UInt64(0)
        self.reserved_principal = UInt64(0)

        assert terms.initial_exchange_date > Global.latest_timestamp, err.INVALID_IED
        assert terms.initial_exchange_date > initial_state.status_date, err.INVALID_IED
        assert terms.initial_exchange_date < terms.maturity_date, err.INVALID_IED

    ############################################################################
    # Update Schedule
    ############################################################################

    def _store_contract_schedule_page(
        self,
        *,
        contract_type: UInt64,
        schedule_page_index: UInt64,
        is_last_page: bool,
        schedule_page: typ.ExecutionSchedulePage,
    ) -> None:
        """Validate and persist one normalized schedule page."""

        assert self.status == UInt64(enums.STATUS_INACTIVE), err.ALREADY_CONFIGURED
        assert schedule_page.length <= UInt64(
            cst.SCHEDULE_PAGE_SIZE
        ), err.INVALID_SCHEDULE_PAGE
        assert self.initial_exchange_amount > UInt64(0), err.TERMS_NOT_CONFIGURED

        page_cursor = schedule_page_index * UInt64(cst.SCHEDULE_PAGE_SIZE)
        page_length = schedule_page.length
        # Validation cost grows with page length, so configuration explicitly
        # buys extra opcode budget for larger uploads.
        ensure_budget(
            required_budget=(
                UInt64(cst.OP_UP_CONTRACT_CONFIG_BASE_BUDGET)
                + page_length * UInt64(cst.OP_UP_CONTRACT_CONFIG_PER_ENTRY_BUDGET)
            ),
        )
        index = UInt64(0)
        while index < page_length:
            entry = schedule_page[index].copy()
            entry_event_type = entry.event_type.as_uint64()
            assert entry.event_id == page_cursor + index, err.INVALID_EVENT_ID
            self._assert_event_allowed_for_contract_type(
                contract_type, entry_event_type
            )
            assert entry.scheduled_time > UInt64(0), err.INVALID_ACTUS_CONFIG
            if entry.event_id > UInt64(0):
                if index > UInt64(0):
                    previous_entry = schedule_page[index - UInt64(1)].copy()
                else:
                    # The first entry of a page must still be ordered after the
                    # last entry of the previous page.
                    assert schedule_page_index > UInt64(0), err.INVALID_EVENT_ID
                    previous_page_index = schedule_page_index - UInt64(1)
                    assert (
                        previous_page_index in self.schedule_page
                    ), err.INVALID_SCHEDULE_PAGE
                    previous_page = self.schedule_page[previous_page_index].copy()
                    assert previous_page.length > UInt64(0), err.INVALID_SCHEDULE_PAGE
                    previous_entry = previous_page[
                        previous_page.length - UInt64(1)
                    ].copy()
                assert (
                    previous_entry.scheduled_time <= entry.scheduled_time
                ), err.INVALID_SORTING
            if entry.event_id == UInt64(0):
                assert entry_event_type == UInt64(
                    enums.EVT_IED
                ), err.INVALID_ACTUS_CONFIG
            index += UInt64(1)

        self._store_schedule_page(schedule_page_index, schedule_page)
        if is_last_page:
            self.schedule_entry_count = (
                schedule_page_index * UInt64(cst.SCHEDULE_PAGE_SIZE) + page_length
            )
            self.status = UInt64(enums.STATUS_PENDING_IED)

    def _append_observed_event(self, payload: typ.ObservedEventRequest) -> None:
        """
        Append an authorized observed event to the schedule tail.

        Observed events are runtime schedule entries supplied by an authorized
        caller. Supported only for CLM contracts.
        """
        assert self._supports_observed_events(), err.OBSERVED_EVENT_REQUIRED
        assert payload.event_id == self.schedule_entry_count, err.INVALID_EVENT_ID
        self._assert_event_allowed_for_contract_type(
            self.contract_type, payload.event_type.as_uint64()
        )

        page_index = self._schedule_page_index(self.schedule_entry_count)
        page = typ.ExecutionSchedulePage()
        if page_index in self.schedule_page:
            page = self.schedule_page[page_index].copy()
        assert page.length < UInt64(cst.SCHEDULE_PAGE_SIZE), err.INVALID_SCHEDULE_PAGE
        page.append(
            typ.ExecutionScheduleEntry(
                event_id=payload.event_id,
                event_type=payload.event_type,
                scheduled_time=payload.scheduled_time,
                accrual_factor=payload.accrual_factor,
                redemption_accrual_factor=payload.redemption_accrual_factor,
                next_nominal_interest_rate=payload.next_nominal_interest_rate,
                next_principal_redemption=payload.next_principal_redemption,
                next_outstanding_principal=payload.next_outstanding_principal,
                flags=payload.flags,
            )
        )
        self.schedule_page[page_index] = page.copy()
        self.schedule_entry_count += UInt64(1)

    def _append_observed_cash_event(self, payload: typ.ObservedCashEventRequest) -> None:
        """
        Append an authorized observed cash event to the schedule tail.

        This v1 path is intentionally narrow: only CLM observed `PR` events may
        be appended, and they must preserve the append-only schedule ordering.
        """
        assert self._supports_observed_events(), err.OBSERVED_EVENT_REQUIRED
        assert payload.event_id == self.schedule_entry_count, err.INVALID_EVENT_ID
        assert payload.event_type == arc4.UInt8(enums.EVT_PR), err.INVALID_EVENT_TYPE
        assert payload.flags & UInt64(enums.FLAG_CASH_EVENT), err.INVALID_ACTUS_CONFIG

        if self.schedule_entry_count > UInt64(0):
            previous_entry = self._get_schedule_entry(self.schedule_entry_count - UInt64(1))
            assert (
                previous_entry.scheduled_time <= payload.scheduled_time
            ), err.INVALID_SORTING

        page_index = self._schedule_page_index(self.schedule_entry_count)
        page = typ.ExecutionSchedulePage()
        if page_index in self.schedule_page:
            page = self.schedule_page[page_index].copy()
        assert page.length < UInt64(cst.SCHEDULE_PAGE_SIZE), err.INVALID_SCHEDULE_PAGE
        page.append(
            typ.ExecutionScheduleEntry(
                event_id=payload.event_id,
                event_type=payload.event_type,
                scheduled_time=payload.scheduled_time,
                accrual_factor=payload.accrual_factor,
                redemption_accrual_factor=payload.redemption_accrual_factor,
                next_nominal_interest_rate=payload.next_nominal_interest_rate,
                next_principal_redemption=payload.next_principal_redemption,
                next_outstanding_principal=payload.next_outstanding_principal,
                flags=payload.flags,
            )
        )
        self.schedule_page[page_index] = page.copy()
        self.schedule_entry_count += UInt64(1)

    ############################################################################
    # Public ABI
    ############################################################################

    @arc4.abimethod(create="require")
    def contract_create(self, *, arranger: Account) -> typ.TimeStamp:
        """
        Create a new D-ASA contract and set the Arranger role

        Args:
            arranger: D-ASA Arranger Address

        Returns:
            UNIX timestamp of contract creation
        """
        self.arranger.value = arranger
        return Global.latest_timestamp

    @arc4.abimethod
    def contract_config(
        self,
        *,
        terms: typ.NormalizedActusTerms,
        initial_state: typ.InitialKernelState,
        prospectus: typ.Prospectus,
    ) -> UInt64:
        """
        Partial contract configuration with: normalized ACTUS terms, initial kernel
        state (pre-IED), prospectus (informational only). The contract stays inactive
        until all schedule pages are configured next.

        Args:
            terms: Normalized ACTUS terms
            initial_state: Initial kernel state (pre-IED)
            prospectus: Prospectus (informational only)

        Returns:
            UNIX timestamp of contract configuration

        Raises:
            UNAUTHORIZED: Not authorized
            ALREADY_CONFIGURED: Contract already configured
            INVALID_ACTUS_CONFIG: Invalid ACTUS configuration
            INVALID_DAY_COUNT_CONVENTION: Invalid day-count convention ID
            INVALID_IED: IED must be set in the future
            INVALID_SORTING: Time events are not sorted correctly
        """
        self._assert_caller_is_arranger()

        # Configure Contract
        self.contract_type = terms.contract_type.as_uint64()
        self._assert_supported_contract_type(self.contract_type)
        self._store_contract_config(self.contract_type, terms, initial_state)

        # Notarize prospectus (optional)
        self.prospectus_hash = prospectus.hash.bytes
        self.prospectus_url = prospectus.url
        return Global.latest_timestamp

    @arc4.abimethod
    def contract_schedule(
        self,
        *,
        schedule_page_index: UInt64,
        is_last_page: bool,
        schedule_page: typ.ExecutionSchedulePage,
    ) -> UInt64:
        """
        Upload one normalized schedule page.

        The configuration operation is considered complete only when the last
        page is stored. At that point `schedule_entry_count` is finalized and
        the contract moves to `STATUS_PENDING_IED`.
        """
        self._assert_caller_is_arranger()

        self._store_contract_schedule_page(
            contract_type=self.contract_type,
            schedule_page_index=schedule_page_index,
            is_last_page=is_last_page,
            schedule_page=schedule_page,
        )
        return Global.latest_timestamp

    @arc4.abimethod
    def contract_execute_ied(self) -> UInt64:
        """Execute the first due `IED` entry and activate the contract.

        `IED` is the one non-cash event that moves the app from
        `STATUS_PENDING_IED` to `STATUS_ACTIVE`.
        """
        self._assert_configured()
        self._assert_caller_is_arranger()
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()

        assert self.event_cursor < self.schedule_entry_count, err.INVALID_EVENT_CURSOR
        entry = self._get_schedule_entry(self.event_cursor)
        assert entry.event_type == arc4.UInt8(enums.EVT_IED), err.INVALID_EVENT_TYPE
        self._apply_non_cash_schedule_entry(
            entry,
            typ.ObservedEventRequest(
                event_id=entry.event_id,
                event_type=entry.event_type,
                scheduled_time=entry.scheduled_time,
                accrual_factor=entry.accrual_factor,
                redemption_accrual_factor=entry.redemption_accrual_factor,
                observed_rate=UInt64(0),
                next_nominal_interest_rate=entry.next_nominal_interest_rate,
                next_principal_redemption=entry.next_principal_redemption,
                next_outstanding_principal=entry.next_outstanding_principal,
                flags=entry.flags,
            ),
        )
        return Global.latest_timestamp

    @arc4.abimethod
    def apply_non_cash_event(
        self,
        *,
        event_id: UInt64,
        payload: typ.ObservedEventRequest,
    ) -> UInt64:
        """Apply the next due non-cash event, optionally appending one first.

        Observed payloads are appended before execution when flagged. Rate reset
        events require the interest oracle because they can change the running
        nominal rate; other non-cash events stay arranger-controlled.
        """
        self._assert_configured()
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()

        if payload.flags & UInt64(enums.FLAG_OBSERVED_EVENT):
            assert self._supports_observed_events(), err.OBSERVED_EVENT_REQUIRED
            self._assert_caller_is_arranger()
            self._append_observed_event(payload)

        assert event_id == self.event_cursor, err.INVALID_EVENT_CURSOR
        entry = self._get_schedule_entry(event_id)
        assert self._event_is_non_cash(
            entry.event_type.as_uint64()
        ), err.INVALID_EVENT_TYPE
        assert entry.event_type != arc4.UInt8(enums.EVT_IED), err.INVALID_EVENT_TYPE
        if self._event_is_rate_reset(entry.event_type.as_uint64()):
            self._assert_caller_is_observer()
        else:
            self._assert_caller_is_arranger()
        self._apply_non_cash_schedule_entry(entry, payload)
        return Global.latest_timestamp

    @arc4.abimethod
    def append_observed_cash_event(
        self,
        *,
        payload: typ.ObservedCashEventRequest,
    ) -> UInt64:
        """Append an arranger-authorized observed cash event to the schedule tail."""
        self._assert_configured()
        self._assert_caller_is_arranger()
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()
        self._assert_initial_exchange_executed()

        self._append_observed_cash_event(payload)
        return Global.latest_timestamp

    @arc4.abimethod(readonly=True)
    def contract_get_state(self) -> typ.KernelState:
        """Return a readonly snapshot of the generic ACTUS kernel state."""
        self._assert_configured()
        return typ.KernelState(
            contract_type=arc4.UInt8(self.contract_type),
            status=self.status,
            total_units=self.total_units,
            reserved_units_total=self.reserved_units_total,
            initial_exchange_amount=self.initial_exchange_amount,
            event_cursor=self.event_cursor,
            schedule_entry_count=self.schedule_entry_count,
            outstanding_principal=self.outstanding_principal,
            interest_calculation_base=self.interest_calculation_base,
            nominal_interest_rate=self.nominal_interest_rate,
            accrued_interest=self.accrued_interest,
            cumulative_interest_index=self.cumulative_interest_index,
            cumulative_principal_index=self.cumulative_principal_index,
            reserved_interest=self.reserved_interest,
            reserved_principal=self.reserved_principal,
        )

    @arc4.abimethod(readonly=True)
    def contract_get_next_due_event(self) -> typ.ExecutionScheduleEntry:
        """Return the next boxed schedule entry, or a zeroed sentinel if ended."""
        self._assert_configured()
        if self.event_cursor >= self.schedule_entry_count:
            return typ.ExecutionScheduleEntry(
                event_id=self.event_cursor,
                event_type=arc4.UInt8(0),
                scheduled_time=UInt64(0),
                accrual_factor=UInt64(0),
                redemption_accrual_factor=UInt64(0),
                next_nominal_interest_rate=UInt64(0),
                next_principal_redemption=UInt64(0),
                next_outstanding_principal=UInt64(0),
                flags=UInt64(0),
            )
        return self._get_schedule_entry(self.event_cursor)
