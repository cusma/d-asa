# This file is auto-generated, do not modify
# flake8: noqa
# fmt: off
import typing

import algopy

class CashFundingResult(algopy.arc4.Struct):
    funded_interest: algopy.arc4.UIntN[typing.Literal[64]]
    funded_principal: algopy.arc4.UIntN[typing.Literal[64]]
    total_funded: algopy.arc4.UIntN[typing.Literal[64]]
    processed_events: algopy.arc4.UIntN[typing.Literal[64]]
    timestamp: algopy.arc4.UIntN[typing.Literal[64]]

class CashClaimResult(algopy.arc4.Struct):
    interest_amount: algopy.arc4.UIntN[typing.Literal[64]]
    principal_amount: algopy.arc4.UIntN[typing.Literal[64]]
    total_amount: algopy.arc4.UIntN[typing.Literal[64]]
    timestamp: algopy.arc4.UIntN[typing.Literal[64]]
    context: algopy.arc4.DynamicBytes

class AccountPosition(algopy.arc4.Struct):
    payment_address: algopy.arc4.Address
    units: algopy.arc4.UIntN[typing.Literal[64]]
    reserved_units: algopy.arc4.UIntN[typing.Literal[64]]
    suspended: algopy.arc4.Bool
    settled_cursor: algopy.arc4.UIntN[typing.Literal[64]]
    interest_checkpoint: algopy.arc4.UIntN[typing.Literal[64]]
    principal_checkpoint: algopy.arc4.UIntN[typing.Literal[64]]
    claimable_interest: algopy.arc4.UIntN[typing.Literal[64]]
    claimable_principal: algopy.arc4.UIntN[typing.Literal[64]]

class NormalizedActusTerms(algopy.arc4.Struct):
    contract_type: algopy.arc4.UIntN[typing.Literal[8]]
    denomination_asset_id: algopy.arc4.UIntN[typing.Literal[64]]
    settlement_asset_id: algopy.arc4.UIntN[typing.Literal[64]]
    total_units: algopy.arc4.UIntN[typing.Literal[64]]
    notional_principal: algopy.arc4.UIntN[typing.Literal[64]]
    initial_exchange_amount: algopy.arc4.UIntN[typing.Literal[64]]
    initial_exchange_date: algopy.arc4.UIntN[typing.Literal[64]]
    maturity_date: algopy.arc4.UIntN[typing.Literal[64]]
    day_count_convention: algopy.arc4.UIntN[typing.Literal[8]]
    rate_reset_spread: algopy.arc4.UIntN[typing.Literal[64]]
    rate_reset_multiplier: algopy.arc4.UIntN[typing.Literal[64]]
    rate_reset_floor: algopy.arc4.UIntN[typing.Literal[64]]
    rate_reset_cap: algopy.arc4.UIntN[typing.Literal[64]]
    rate_reset_next: algopy.arc4.UIntN[typing.Literal[64]]
    has_rate_reset_floor: algopy.arc4.Bool
    has_rate_reset_cap: algopy.arc4.Bool
    dynamic_principal_redemption: algopy.arc4.Bool
    fixed_point_scale: algopy.arc4.UIntN[typing.Literal[64]]

class InitialKernelState(algopy.arc4.Struct):
    status_date: algopy.arc4.UIntN[typing.Literal[64]]
    event_cursor: algopy.arc4.UIntN[typing.Literal[64]]
    outstanding_principal: algopy.arc4.UIntN[typing.Literal[64]]
    interest_calculation_base: algopy.arc4.UIntN[typing.Literal[64]]
    nominal_interest_rate: algopy.arc4.UIntN[typing.Literal[64]]
    accrued_interest: algopy.arc4.UIntN[typing.Literal[64]]
    next_principal_redemption: algopy.arc4.UIntN[typing.Literal[64]]
    cumulative_interest_index: algopy.arc4.UIntN[typing.Literal[64]]
    cumulative_principal_index: algopy.arc4.UIntN[typing.Literal[64]]

class Prospectus(algopy.arc4.Struct):
    hash: algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]]
    url: algopy.arc4.String

class ObservedEventRequest(algopy.arc4.Struct):
    event_id: algopy.arc4.UIntN[typing.Literal[64]]
    event_type: algopy.arc4.UIntN[typing.Literal[8]]
    scheduled_time: algopy.arc4.UIntN[typing.Literal[64]]
    accrual_factor: algopy.arc4.UIntN[typing.Literal[64]]
    redemption_accrual_factor: algopy.arc4.UIntN[typing.Literal[64]]
    observed_rate: algopy.arc4.UIntN[typing.Literal[64]]
    next_nominal_interest_rate: algopy.arc4.UIntN[typing.Literal[64]]
    next_principal_redemption: algopy.arc4.UIntN[typing.Literal[64]]
    next_outstanding_principal: algopy.arc4.UIntN[typing.Literal[64]]
    flags: algopy.arc4.UIntN[typing.Literal[64]]

class ObservedCashEventRequest(algopy.arc4.Struct):
    event_id: algopy.arc4.UIntN[typing.Literal[64]]
    event_type: algopy.arc4.UIntN[typing.Literal[8]]
    scheduled_time: algopy.arc4.UIntN[typing.Literal[64]]
    accrual_factor: algopy.arc4.UIntN[typing.Literal[64]]
    redemption_accrual_factor: algopy.arc4.UIntN[typing.Literal[64]]
    next_nominal_interest_rate: algopy.arc4.UIntN[typing.Literal[64]]
    next_principal_redemption: algopy.arc4.UIntN[typing.Literal[64]]
    next_outstanding_principal: algopy.arc4.UIntN[typing.Literal[64]]
    flags: algopy.arc4.UIntN[typing.Literal[64]]

class KernelState(algopy.arc4.Struct):
    contract_type: algopy.arc4.UIntN[typing.Literal[8]]
    status: algopy.arc4.UIntN[typing.Literal[64]]
    total_units: algopy.arc4.UIntN[typing.Literal[64]]
    reserved_units_total: algopy.arc4.UIntN[typing.Literal[64]]
    initial_exchange_amount: algopy.arc4.UIntN[typing.Literal[64]]
    event_cursor: algopy.arc4.UIntN[typing.Literal[64]]
    schedule_entry_count: algopy.arc4.UIntN[typing.Literal[64]]
    outstanding_principal: algopy.arc4.UIntN[typing.Literal[64]]
    interest_calculation_base: algopy.arc4.UIntN[typing.Literal[64]]
    nominal_interest_rate: algopy.arc4.UIntN[typing.Literal[64]]
    accrued_interest: algopy.arc4.UIntN[typing.Literal[64]]
    cumulative_interest_index: algopy.arc4.UIntN[typing.Literal[64]]
    cumulative_principal_index: algopy.arc4.UIntN[typing.Literal[64]]
    reserved_interest: algopy.arc4.UIntN[typing.Literal[64]]
    reserved_principal: algopy.arc4.UIntN[typing.Literal[64]]

class ExecutionScheduleEntry(algopy.arc4.Struct):
    event_id: algopy.arc4.UIntN[typing.Literal[64]]
    event_type: algopy.arc4.UIntN[typing.Literal[8]]
    scheduled_time: algopy.arc4.UIntN[typing.Literal[64]]
    accrual_factor: algopy.arc4.UIntN[typing.Literal[64]]
    redemption_accrual_factor: algopy.arc4.UIntN[typing.Literal[64]]
    next_nominal_interest_rate: algopy.arc4.UIntN[typing.Literal[64]]
    next_principal_redemption: algopy.arc4.UIntN[typing.Literal[64]]
    next_outstanding_principal: algopy.arc4.UIntN[typing.Literal[64]]
    flags: algopy.arc4.UIntN[typing.Literal[64]]

class RoleValidity(algopy.arc4.Struct):
    role_validity_start: algopy.arc4.UIntN[typing.Literal[64]]
    role_validity_end: algopy.arc4.UIntN[typing.Literal[64]]

class DASA(algopy.arc4.ARC4Client, typing.Protocol):
    """
    Debt Algorand Standard Application.
    """
    @algopy.arc4.abimethod
    def fund_due_cashflows(
        self,
        max_event_count: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> CashFundingResult:
        """
        Reserve due ACTUS cash events into the escrow-style claim ledger.
        """

    @algopy.arc4.abimethod
    def claim_due_cashflows(
        self,
        holding_address: algopy.arc4.Address,
        payment_info: algopy.arc4.DynamicBytes,
    ) -> CashClaimResult:
        """
        Withdraw the holder's already funded ACTUS cash entitlements.
        """

    @algopy.arc4.abimethod
    def transfer_set_schedule(
        self,
        open_date: algopy.arc4.UIntN[typing.Literal[64]],
        closure_date: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Configure the secondary-market transfer window.
        """

    @algopy.arc4.abimethod
    def primary_distribution(
        self,
        holding_address: algopy.arc4.Address,
        units: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Reserve units for a holder before the initial exchange activates issuance.
        """

    @algopy.arc4.abimethod
    def transfer(
        self,
        sender_holding_address: algopy.arc4.Address,
        receiver_holding_address: algopy.arc4.Address,
        units: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Transfer active units after settling both counterparties to the current cursor.
        Returns the number of units moved. The ACTUS kernel no longer persists a nominal per-unit value on-chain, so transfer results are unit-based.
        """

    @algopy.arc4.abimethod
    def account_suspension(
        self,
        holding_address: algopy.arc4.Address,
        suspended: algopy.arc4.Bool,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Set the suspension status of one account.
        """

    @algopy.arc4.abimethod
    def account_open(
        self,
        holding_address: algopy.arc4.Address,
        payment_address: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Open a contract account with a new position and register its payment address.
        """

    @algopy.arc4.abimethod
    def account_update_payment_address(
        self,
        holding_address: algopy.arc4.Address,
        payment_address: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Update the payment address of an account.
        """

    @algopy.arc4.abimethod(readonly=True)
    def account_get_position(
        self,
        holding_address: algopy.arc4.Address,
    ) -> AccountPosition:
        """
        Get the full accounting position for one holder.
        """

    @algopy.arc4.abimethod(create='require')
    def contract_create(
        self,
        arranger: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Create a new D-ASA contract and set the arranger role.
        """

    @algopy.arc4.abimethod
    def contract_config(
        self,
        terms: NormalizedActusTerms,
        initial_state: InitialKernelState,
        prospectus: Prospectus,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Partial contract configuration with: normalized ACTUS terms, initial kernel
        state (pre-IED), prospectus (informational only). The contract stays inactive until all schedule pages are configured next.
        """

    @algopy.arc4.abimethod
    def contract_schedule(
        self,
        schedule_page_index: algopy.arc4.UIntN[typing.Literal[64]],
        is_last_page: algopy.arc4.Bool,
        schedule_page: algopy.arc4.DynamicArray[algopy.arc4.Tuple[algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[8]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]]]],
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Upload one normalized schedule page.
        The configuration operation is considered complete only when the last page is stored. At that point `schedule_entry_count` is finalized and the contract moves to `STATUS_PENDING_IED`.
        """

    @algopy.arc4.abimethod
    def contract_execute_ied(
        self,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Execute the first due `IED` entry and activate the contract.
        `IED` is the one non-cash event that moves the app from `STATUS_PENDING_IED` to `STATUS_ACTIVE`.
        """

    @algopy.arc4.abimethod
    def apply_non_cash_event(
        self,
        event_id: algopy.arc4.UIntN[typing.Literal[64]],
        payload: ObservedEventRequest,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Apply the next due non-cash event, optionally appending one first.
        Observed payloads are appended before execution when flagged. Rate reset events require the interest oracle because they can change the running nominal rate; other non-cash events stay arranger-controlled.
        """

    @algopy.arc4.abimethod
    def append_observed_cash_event(
        self,
        payload: ObservedCashEventRequest,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Append an arranger-authorized observed cash event to the schedule tail.
        """

    @algopy.arc4.abimethod(readonly=True)
    def contract_get_state(
        self,
    ) -> KernelState:
        """
        Return a readonly snapshot of the generic ACTUS kernel state.
        """

    @algopy.arc4.abimethod(readonly=True)
    def contract_get_next_due_event(
        self,
    ) -> ExecutionScheduleEntry:
        """
        Return the next boxed schedule entry, or a zeroed sentinel if ended.
        """

    @algopy.arc4.abimethod(allow_actions=['UpdateApplication'])
    def contract_update(
        self,
    ) -> None:
        """
        Update D-ASA application.
        """

    @algopy.arc4.abimethod
    def rbac_rotate_arranger(
        self,
        new_arranger: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Rotate the arranger address.
        """

    @algopy.arc4.abimethod
    def rbac_set_op_daemon(
        self,
        address: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Non-normative helper to set the operation daemon address.
        """

    @algopy.arc4.abimethod
    def rbac_assign_role(
        self,
        role_id: algopy.arc4.UIntN[typing.Literal[8]],
        role_address: algopy.arc4.Address,
        validity: RoleValidity,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Assign a role to an address.
        """

    @algopy.arc4.abimethod
    def rbac_revoke_role(
        self,
        role_id: algopy.arc4.UIntN[typing.Literal[8]],
        role_address: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Revoke a role from an address.
        """

    @algopy.arc4.abimethod
    def rbac_contract_suspension(
        self,
        suspended: algopy.arc4.Bool,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Set the asset-wide suspension status.
        """

    @algopy.arc4.abimethod
    def rbac_contract_default(
        self,
        defaulted: algopy.arc4.Bool,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Set D-ASA default status
        """

    @algopy.arc4.abimethod(readonly=True)
    def rbac_get_arranger(
        self,
    ) -> algopy.arc4.Address:
        """
        Get the arranger address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def rbac_get_address_roles(
        self,
        address: algopy.arc4.Address,
    ) -> algopy.arc4.Tuple[algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.Bool]:
        """
        Non-normative helper to get the active roles assigned to an address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def rbac_get_role_validity(
        self,
        role_id: algopy.arc4.UIntN[typing.Literal[8]],
        role_address: algopy.arc4.Address,
    ) -> RoleValidity:
        """
        Get the stored validity interval for a role assignment.
        """
