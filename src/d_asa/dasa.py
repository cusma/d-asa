from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
from typing import Literal, cast

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AssetTransferParams,
    CommonAppCallParams,
    PaymentParams,
    SendParams,
    SigningAccount,
)
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.constants import ZERO_ADDRESS
from algosdk.transaction import Transaction
from algosdk.v2client.models import SimulateTraceConfig

from . import constants as cst
from . import enums
from ._dasa_mappers import (
    to_client_initial_state,
    to_client_observed_cash_event,
    to_client_observed_event,
    to_client_prospectus,
    to_client_role_validity,
    to_client_schedule_page,
    to_client_terms,
    to_sdk_account_position,
    to_sdk_schedule_entry,
)
from .artifacts.dasa_client import (
    AccountOpenArgs,
    AccountSuspensionArgs,
    AccountUpdatePaymentAddressArgs,
    AppendObservedCashEventArgs,
    ApplyNonCashEventArgs,
    CashClaimResult,
    CashFundingResult,
    ClaimDueCashflowsArgs,
    ContractConfigArgs,
    ContractCreateArgs,
    ContractScheduleArgs,
    FundDueCashflowsArgs,
    PrimaryDistributionArgs,
    RbacAssignRoleArgs,
    RbacContractDefaultArgs,
    RbacContractSuspensionArgs,
    RbacRevokeRoleArgs,
    RbacRotateArrangerArgs,
    RbacSetOpDaemonArgs,
    TransferArgs,
    TransferSetScheduleArgs,
)
from .artifacts.dasa_client import (
    DasaClient as _GeneratedDasaClient,
)
from .artifacts.dasa_client import (
    DasaComposer as _GeneratedDasaComposer,
)
from .artifacts.dasa_client import (
    DasaFactory as _GeneratedDasaFactory,
)
from .contracts import ContractAttributes
from .day_count import year_fraction_fixed
from .models import (
    AccountPosition,
    ExecutionScheduleEntry,
    NormalizationResult,
    ObservedCashEventRequest,
    ObservedEventRequest,
)
from .normalization import normalize_contract_attributes

DEFAULT_APP_FUNDING = AlgoAmount.from_algo(2)
DEFAULT_CLAIM_FEE = AlgoAmount.from_micro_algo(3_000)
DEFAULT_CONFIG_FEE = AlgoAmount.from_micro_algo(5_000)
DEFAULT_ROLE_VALIDITY_END = 2**64 - 1
_MANAGED_ROLE_IDS = frozenset(
    {
        enums.ROLE_ACCOUNT_MANAGER,
        enums.ROLE_PRIMARY_DEALER,
        enums.ROLE_TRUSTEE,
        enums.ROLE_AUTHORITY,
        enums.ROLE_OBSERVER,
    }
)


class DAsaRole(IntEnum):
    ARRANGER = enums.ROLE_ARRANGER
    OP_DAEMON = enums.ROLE_OP_DAEMON
    ACCOUNT_MANAGER = enums.ROLE_ACCOUNT_MANAGER
    PRIMARY_DEALER = enums.ROLE_PRIMARY_DEALER
    TRUSTEE = enums.ROLE_TRUSTEE
    AUTHORITY = enums.ROLE_AUTHORITY
    OBSERVER = enums.ROLE_OBSERVER


@dataclass(frozen=True, slots=True)
class RoleValidityWindow:
    start: int
    end: int

    def is_active(self, timestamp: int) -> bool:
        return self.start <= timestamp <= self.end


@dataclass(frozen=True, slots=True)
class PricingContext:
    notional_unit_value: int

    def __post_init__(self) -> None:
        if self.notional_unit_value <= 0:
            raise ValueError("notional_unit_value must be positive")


@dataclass(frozen=True, slots=True)
class AddressRoles:
    arranger: bool
    op_daemon: bool
    account_manager: bool
    primary_dealer: bool
    trustee: bool
    authority: bool
    observer: bool


@dataclass(frozen=True, slots=True)
class ContractState:
    arranger: str
    op_daemon: str
    contract_suspended: bool
    defaulted: bool
    status: int
    contract_type: int
    denomination_asset_id: int
    settlement_asset_id: int
    initial_exchange_date: int
    maturity_date: int
    transfer_opening_date: int
    transfer_closure_date: int
    day_count_convention: int
    total_units: int
    reserved_units_total: int
    initial_exchange_amount: int
    outstanding_principal: int
    next_principal_redemption: int
    dynamic_principal_redemption: bool
    interest_calculation_base: int
    accrued_interest: int
    nominal_interest_rate: int
    rate_reset_spread: int
    rate_reset_multiplier: int
    rate_reset_floor: int
    rate_reset_cap: int
    rate_reset_next: int
    has_rate_reset_floor: bool
    has_rate_reset_cap: bool
    reserved_principal: int
    reserved_interest: int
    cumulative_interest_index: int
    cumulative_principal_index: int
    event_cursor: int
    schedule_entry_count: int
    fixed_point_scale: int


@dataclass(frozen=True, slots=True)
class FundingResult:
    funded_interest: int
    funded_principal: int
    total_funded: int
    processed_events: int
    timestamp: int


@dataclass(frozen=True, slots=True)
class ClaimResult:
    interest_amount: int
    principal_amount: int
    total_amount: int
    timestamp: int
    context: bytes


@dataclass(frozen=True, slots=True)
class AccountValuation:
    valuation_timestamp: int
    position: AccountPosition
    principal_share: int
    claimable_interest: int
    claimable_principal: int
    accrued_interest_not_due: int
    economic_value_total: int


@dataclass(frozen=True, slots=True)
class TradeQuoteInput:
    clean_total_base_units: int | None = None
    clean_per_unit_base_units: Decimal | int | str | None = None
    clean_price_per_100: Decimal | int | str | None = None

    def resolve(self, *, units: int, pricing_context: PricingContext | None) -> Decimal:
        supplied = [
            self.clean_total_base_units is not None,
            self.clean_per_unit_base_units is not None,
            self.clean_price_per_100 is not None,
        ]
        if sum(supplied) != 1:
            raise ValueError("exactly one clean quote input must be supplied")

        if self.clean_total_base_units is not None:
            return Decimal(self.clean_total_base_units)

        if self.clean_per_unit_base_units is not None:
            return Decimal(str(self.clean_per_unit_base_units)) * Decimal(units)

        if pricing_context is None:
            raise ValueError(
                "clean_price_per_100 requires a pricing context with notional_unit_value"
            )
        return (
            Decimal(str(self.clean_price_per_100))
            / Decimal(100)
            * Decimal(pricing_context.notional_unit_value)
            * Decimal(units)
        )


@dataclass(frozen=True, slots=True)
class TradeQuote:
    trade_side: Literal["buy", "sell"]
    units: int
    valuation_timestamp: int
    principal_share_total: int
    accrued_interest_not_due_total: int
    economic_value_total: int
    seller_retained_claimable_interest: int
    seller_retained_claimable_principal: int
    par_reference_clean_total: int
    par_reference_dirty_total: int
    market_clean_total: Decimal | None = None
    market_dirty_total: Decimal | None = None
    market_clean_per_unit: Decimal | None = None
    market_dirty_per_unit: Decimal | None = None


@dataclass(frozen=True, slots=True)
class OtcDvpDraft:
    buyer_address: str
    seller_address: str
    sender_holding_address: str
    receiver_holding_address: str
    units: int
    payment_amount: int
    payment_asset_id: int | None
    payment_transaction: Transaction
    quote: TradeQuote | None
    composer: _GeneratedDasaComposer

    def send(self, send_params: SendParams | None = None) -> object:
        return self.composer.send(send_params)

    def simulate(
        self,
        *,
        allow_more_logs: bool | None = None,
        allow_empty_signatures: bool | None = None,
        allow_unnamed_resources: bool | None = None,
        extra_opcode_budget: int | None = None,
        exec_trace_config: SimulateTraceConfig | None = None,
        simulation_round: int | None = None,
        skip_signatures: bool | None = None,
    ) -> object:
        return self.composer.simulate(
            allow_more_logs=allow_more_logs,
            allow_empty_signatures=allow_empty_signatures,
            allow_unnamed_resources=allow_unnamed_resources,
            extra_opcode_budget=extra_opcode_budget,
            exec_trace_config=exec_trace_config,
            simulation_round=simulation_round,
            skip_signatures=skip_signatures,
        )


def _scaled_mul_div(multiplicand: int, multiplier: int, divisor: int) -> int:
    if multiplicand == 0 or multiplier == 0:
        return 0
    return multiplicand * multiplier // divisor


def _amount_to_index_delta(
    amount: int, *, total_units: int, fixed_point_scale: int
) -> int:
    if amount == 0:
        return 0
    if total_units <= 0:
        raise ValueError("total_units must be positive")
    return _scaled_mul_div(amount, fixed_point_scale, total_units)


def _index_delta_to_amount(
    index_delta: int,
    *,
    units: int,
    fixed_point_scale: int,
) -> int:
    if index_delta == 0 or units == 0:
        return 0
    return _scaled_mul_div(units, index_delta, fixed_point_scale)


def _share_amount(
    amount: int,
    *,
    units: int,
    total_units: int,
    fixed_point_scale: int,
) -> int:
    index_delta = _amount_to_index_delta(
        amount,
        total_units=total_units,
        fixed_point_scale=fixed_point_scale,
    )
    return _index_delta_to_amount(
        index_delta,
        units=units,
        fixed_point_scale=fixed_point_scale,
    )


def _latest_timestamp(client: _GeneratedDasaClient) -> int:
    algod = client.algorand.client.algod
    status = cast(dict[str, int], algod.status())
    block_info = cast(dict[str, object], algod.block_info(status["last-round"]))
    block = cast(dict[str, int], block_info["block"])
    return int(block["ts"])


def _normalize_result(
    *,
    normalized: NormalizationResult | None,
    contract: ContractAttributes | None,
    denomination_asset_id: int | None,
    denomination_asset_decimals: int | None,
    notional_unit_value: int | float | Decimal | None,
    secondary_market_opening_date: int | None,
    secondary_market_closure_date: int | None,
    preprocessed_events: Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None,
) -> NormalizationResult:
    if normalized is not None:
        if contract is not None:
            raise ValueError("pass either normalized or contract attributes, not both")
        return normalized

    if contract is None:
        raise ValueError("normalized or contract attributes are required")

    required_values = {
        "denomination_asset_id": denomination_asset_id,
        "denomination_asset_decimals": denomination_asset_decimals,
        "notional_unit_value": notional_unit_value,
        "secondary_market_opening_date": secondary_market_opening_date,
        "secondary_market_closure_date": secondary_market_closure_date,
    }
    missing = [name for name, value in required_values.items() if value is None]
    if missing:
        raise ValueError(
            f"missing normalization inputs for contract attributes: {', '.join(missing)}"
        )

    return normalize_contract_attributes(
        contract,
        denomination_asset_id=cast(int, denomination_asset_id),
        denomination_asset_decimals=cast(int, denomination_asset_decimals),
        notional_unit_value=cast(int | float | Decimal, notional_unit_value),
        secondary_market_opening_date=cast(int, secondary_market_opening_date),
        secondary_market_closure_date=cast(int, secondary_market_closure_date),
        preprocessed_events=preprocessed_events,
    )


def _maybe_activate_reserved_units(
    position: AccountPosition,
    *,
    state: ContractState,
) -> AccountPosition:
    if state.status == enums.STATUS_PENDING_IED or position.reserved_units == 0:
        return position
    return AccountPosition(
        units=position.units + position.reserved_units,
        reserved_units=0,
        payment_address=position.payment_address,
        suspended=position.suspended,
        settled_cursor=position.settled_cursor,
        interest_checkpoint=position.interest_checkpoint,
        principal_checkpoint=position.principal_checkpoint,
        claimable_interest=position.claimable_interest,
        claimable_principal=position.claimable_principal,
    )


def _actualize_position(
    position: AccountPosition, *, state: ContractState
) -> AccountPosition:
    preview = _maybe_activate_reserved_units(position, state=state)
    interest_delta = state.cumulative_interest_index - preview.interest_checkpoint
    principal_delta = state.cumulative_principal_index - preview.principal_checkpoint
    if interest_delta < 0 or principal_delta < 0:
        raise ValueError("account checkpoints are ahead of global cumulative indices")
    claimable_interest = preview.claimable_interest + _index_delta_to_amount(
        interest_delta,
        units=preview.units,
        fixed_point_scale=state.fixed_point_scale,
    )
    claimable_principal = preview.claimable_principal + _index_delta_to_amount(
        principal_delta,
        units=preview.units,
        fixed_point_scale=state.fixed_point_scale,
    )
    return AccountPosition(
        units=preview.units,
        reserved_units=preview.reserved_units,
        payment_address=preview.payment_address,
        suspended=preview.suspended,
        settled_cursor=state.event_cursor,
        interest_checkpoint=state.cumulative_interest_index,
        principal_checkpoint=state.cumulative_principal_index,
        claimable_interest=claimable_interest,
        claimable_principal=claimable_principal,
    )


class ContractView:
    def __init__(
        self,
        client: _GeneratedDasaClient,
        *,
        pricing_context: PricingContext | None = None,
    ) -> None:
        self._client = client
        self._pricing_context = pricing_context

    @property
    def raw_client(self) -> _GeneratedDasaClient:
        return self._client

    @property
    def pricing_context(self) -> PricingContext | None:
        return self._pricing_context

    def get_state(self) -> ContractState:
        global_state = self._client.state.global_state
        return ContractState(
            arranger=global_state.arranger,
            op_daemon=global_state.op_daemon,
            contract_suspended=bool(global_state.contract_suspended),
            defaulted=bool(global_state.defaulted),
            status=global_state.status,
            contract_type=global_state.contract_type,
            denomination_asset_id=global_state.denomination_asset_id,
            settlement_asset_id=global_state.settlement_asset_id,
            initial_exchange_date=global_state.initial_exchange_date,
            maturity_date=global_state.maturity_date,
            transfer_opening_date=global_state.transfer_opening_date,
            transfer_closure_date=global_state.transfer_closure_date,
            day_count_convention=global_state.day_count_convention,
            total_units=global_state.total_units,
            reserved_units_total=global_state.reserved_units_total,
            initial_exchange_amount=global_state.initial_exchange_amount,
            outstanding_principal=global_state.outstanding_principal,
            next_principal_redemption=global_state.next_principal_redemption,
            dynamic_principal_redemption=bool(
                global_state.dynamic_principal_redemption
            ),
            interest_calculation_base=global_state.interest_calculation_base,
            accrued_interest=global_state.accrued_interest,
            nominal_interest_rate=global_state.nominal_interest_rate,
            rate_reset_spread=global_state.rate_reset_spread,
            rate_reset_multiplier=global_state.rate_reset_multiplier,
            rate_reset_floor=global_state.rate_reset_floor,
            rate_reset_cap=global_state.rate_reset_cap,
            rate_reset_next=global_state.rate_reset_next,
            has_rate_reset_floor=bool(global_state.has_rate_reset_floor),
            has_rate_reset_cap=bool(global_state.has_rate_reset_cap),
            reserved_principal=global_state.reserved_principal,
            reserved_interest=global_state.reserved_interest,
            cumulative_interest_index=global_state.cumulative_interest_index,
            cumulative_principal_index=global_state.cumulative_principal_index,
            event_cursor=global_state.event_cursor,
            schedule_entry_count=global_state.schedule_entry_count,
            fixed_point_scale=global_state.fixed_point_scale,
        )

    def get_schedule_entry(self, event_id: int) -> ExecutionScheduleEntry | None:
        state = self.get_state()
        if event_id < 0 or event_id >= state.schedule_entry_count:
            return None
        page_index = event_id // cst.SCHEDULE_PAGE_SIZE
        page_offset = event_id % cst.SCHEDULE_PAGE_SIZE
        page = self._client.state.box.schedule_page.get_value(page_index)
        if page is None or page_offset >= len(page):
            return None
        return to_sdk_schedule_entry(page[page_offset])

    def get_next_due_event(self) -> ExecutionScheduleEntry | None:
        state = self.get_state()
        if state.event_cursor >= state.schedule_entry_count:
            return None
        return self.get_schedule_entry(state.event_cursor)

    def get_arranger(self) -> str:
        return self._client.state.global_state.arranger

    def get_role_validity(
        self,
        role: DAsaRole,
        address: str,
    ) -> RoleValidityWindow | None:
        if role == DAsaRole.ARRANGER:
            return RoleValidityWindow(0, 0) if address == self.get_arranger() else None
        if role == DAsaRole.OP_DAEMON:
            return None
        if int(role) not in _MANAGED_ROLE_IDS:
            raise ValueError(f"unsupported role for validity lookup: {role.name}")

        if role == DAsaRole.ACCOUNT_MANAGER:
            validity = self._client.state.box.account_manager.get_value(address)
        elif role == DAsaRole.PRIMARY_DEALER:
            validity = self._client.state.box.primary_dealer.get_value(address)
        elif role == DAsaRole.TRUSTEE:
            validity = self._client.state.box.trustee.get_value(address)
        elif role == DAsaRole.AUTHORITY:
            validity = self._client.state.box.authority.get_value(address)
        else:
            validity = self._client.state.box.observer.get_value(address)

        if validity is None:
            return None
        return RoleValidityWindow(
            start=validity.role_validity_start,
            end=validity.role_validity_end,
        )

    def get_address_roles(
        self,
        address: str,
        *,
        at_time: int | None = None,
    ) -> AddressRoles:
        if at_time is None:
            timestamp = _latest_timestamp(self._client)
        else:
            timestamp = at_time
        arranger = self._client.state.global_state.arranger
        op_daemon = self._client.state.global_state.op_daemon

        def role_active(role: DAsaRole) -> bool:
            validity = self.get_role_validity(role, address)
            return validity is not None and validity.is_active(timestamp)

        return AddressRoles(
            arranger=address == arranger and arranger != ZERO_ADDRESS,
            op_daemon=address == op_daemon and op_daemon != ZERO_ADDRESS,
            account_manager=role_active(DAsaRole.ACCOUNT_MANAGER),
            primary_dealer=role_active(DAsaRole.PRIMARY_DEALER),
            trustee=role_active(DAsaRole.TRUSTEE),
            authority=role_active(DAsaRole.AUTHORITY),
            observer=role_active(DAsaRole.OBSERVER),
        )


class _BoundRole:
    def __init__(self, app: DAsa, account: SigningAccount) -> None:
        self._app = app
        self._account = account
        self._client = app.raw_client.clone(
            default_sender=account.address,
            default_signer=account.signer,
        )

    @property
    def raw_client(self) -> _GeneratedDasaClient:
        return self._client

    @property
    def account(self) -> SigningAccount:
        return self._account

    @property
    def contract(self) -> ContractView:
        return self._app.contract


class ArrangerRole(_BoundRole):
    def configure(
        self,
        normalized: NormalizationResult,
        *,
        prospectus_url: str = "",
        prospectus_hash: bytes | None = None,
    ) -> int:
        result = self._client.send.contract_config(
            ContractConfigArgs(
                terms=to_client_terms(normalized),
                initial_state=to_client_initial_state(normalized),
                prospectus=to_client_prospectus(
                    url=prospectus_url,
                    hash_bytes=prospectus_hash,
                ),
            ),
            params=CommonAppCallParams(max_fee=DEFAULT_CONFIG_FEE),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )
        return cast(int, result.abi_return)

    def configure_from_attributes(
        self,
        contract: ContractAttributes,
        *,
        denomination_asset_id: int,
        denomination_asset_decimals: int,
        notional_unit_value: int | float | Decimal,
        secondary_market_opening_date: int,
        secondary_market_closure_date: int,
        preprocessed_events: (
            Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None
        ) = None,
        prospectus_url: str = "",
        prospectus_hash: bytes | None = None,
    ) -> NormalizationResult:
        normalized = normalize_contract_attributes(
            contract,
            denomination_asset_id=denomination_asset_id,
            denomination_asset_decimals=denomination_asset_decimals,
            notional_unit_value=notional_unit_value,
            secondary_market_opening_date=secondary_market_opening_date,
            secondary_market_closure_date=secondary_market_closure_date,
            preprocessed_events=preprocessed_events,
        )
        self.configure(
            normalized,
            prospectus_url=prospectus_url,
            prospectus_hash=prospectus_hash,
        )
        return normalized

    def upload_schedule(
        self,
        normalized: NormalizationResult,
        *,
        page_size: int = cst.SCHEDULE_PAGE_SIZE,
    ) -> tuple[int, ...]:
        timestamps: list[int] = []
        pages = normalized.schedule_pages(page_size)
        for index, page in enumerate(pages):
            result = self._client.send.contract_schedule(
                ContractScheduleArgs(
                    schedule_page_index=index,
                    is_last_page=index == len(pages) - 1,
                    schedule_page=to_client_schedule_page(page),
                ),
                params=CommonAppCallParams(max_fee=DEFAULT_CONFIG_FEE),
                send_params=SendParams(cover_app_call_inner_transaction_fees=True),
            )
            timestamps.append(cast(int, result.abi_return))
        return tuple(timestamps)

    def configure_contract(
        self,
        *,
        normalized: NormalizationResult | None = None,
        contract: ContractAttributes | None = None,
        denomination_asset_id: int | None = None,
        denomination_asset_decimals: int | None = None,
        notional_unit_value: int | float | Decimal | None = None,
        secondary_market_opening_date: int | None = None,
        secondary_market_closure_date: int | None = None,
        preprocessed_events: (
            Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None
        ) = None,
        prospectus_url: str = "",
        prospectus_hash: bytes | None = None,
        page_size: int = cst.SCHEDULE_PAGE_SIZE,
        transfer_opening_date: int | None = None,
        transfer_closure_date: int | None = None,
    ) -> NormalizationResult:
        resolved = _normalize_result(
            normalized=normalized,
            contract=contract,
            denomination_asset_id=denomination_asset_id,
            denomination_asset_decimals=denomination_asset_decimals,
            notional_unit_value=notional_unit_value,
            secondary_market_opening_date=secondary_market_opening_date,
            secondary_market_closure_date=secondary_market_closure_date,
            preprocessed_events=preprocessed_events,
        )
        self.configure(
            resolved,
            prospectus_url=prospectus_url,
            prospectus_hash=prospectus_hash,
        )
        self.upload_schedule(resolved, page_size=page_size)
        if transfer_opening_date is not None and transfer_closure_date is not None:
            self.set_transfer_window(
                open_date=transfer_opening_date,
                closure_date=transfer_closure_date,
            )
        self._app._pricing_context = PricingContext(
            notional_unit_value=resolved.terms.notional_unit_value
        )
        self._app.contract._pricing_context = self._app._pricing_context
        return resolved

    def execute_ied(self) -> int:
        result = self._client.send.contract_execute_ied()
        return cast(int, result.abi_return)

    def set_transfer_window(self, *, open_date: int, closure_date: int) -> int:
        if closure_date <= open_date:
            raise ValueError(
                "transfer window closure_date must be strictly after open_date"
            )
        state = self.contract.get_state()
        if not state.initial_exchange_date or open_date < state.initial_exchange_date:
            raise ValueError(
                "transfer window open_date must be at or after initial_exchange_date"
            )
        result = self._client.send.transfer_set_schedule(
            TransferSetScheduleArgs(open_date=open_date, closure_date=closure_date)
        )
        return cast(int, result.abi_return)

    def fund_due_cashflows(self, *, max_event_count: int) -> FundingResult:
        result = self._client.send.fund_due_cashflows(
            FundDueCashflowsArgs(max_event_count=max_event_count)
        )
        funding = cast(CashFundingResult, result.abi_return)
        return FundingResult(
            funded_interest=funding.funded_interest,
            funded_principal=funding.funded_principal,
            total_funded=funding.total_funded,
            processed_events=funding.processed_events,
            timestamp=funding.timestamp,
        )

    def append_observed_cash_event(self, payload: ObservedCashEventRequest) -> int:
        event_id = self.contract.get_state().schedule_entry_count
        result = self._client.send.append_observed_cash_event(
            AppendObservedCashEventArgs(
                payload=to_client_observed_cash_event(payload, event_id=event_id)
            )
        )
        return cast(int, result.abi_return)

    def append_observed_cash_events(
        self,
        payloads: Sequence[ObservedCashEventRequest],
    ) -> tuple[int, ...]:
        timestamps: list[int] = []
        for payload in payloads:
            timestamps.append(self.append_observed_cash_event(payload))
        return tuple(timestamps)

    def apply_non_cash_event(
        self, *, event_id: int, payload: ObservedEventRequest
    ) -> int:
        payload_event_id = (
            self.contract.get_state().schedule_entry_count
            if payload.flags & enums.FLAG_OBSERVED_EVENT
            else event_id
        )
        result = self._client.send.apply_non_cash_event(
            ApplyNonCashEventArgs(
                event_id=event_id,
                payload=to_client_observed_event(payload, event_id=payload_event_id),
            )
        )
        return cast(int, result.abi_return)

    def rotate_arranger(self, new_arranger: str) -> int:
        result = self._client.send.rbac_rotate_arranger(
            RbacRotateArrangerArgs(new_arranger=new_arranger)
        )
        return cast(int, result.abi_return)

    def set_op_daemon(self, address: str) -> int:
        result = self._client.send.rbac_set_op_daemon(
            RbacSetOpDaemonArgs(address=address)
        )
        return cast(int, result.abi_return)

    def assign_role(
        self,
        role: DAsaRole,
        address: str,
        *,
        validity: RoleValidityWindow | None = None,
    ) -> int:
        validity_window = validity or RoleValidityWindow(0, DEFAULT_ROLE_VALIDITY_END)
        if address == ZERO_ADDRESS:
            raise ValueError("role address must not be the Algorand zero address")
        if validity_window.start >= validity_window.end:
            raise ValueError("role validity start must be strictly earlier than end")
        result = self._client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=int(role),
                role_address=address,
                validity=to_client_role_validity(
                    start=validity_window.start,
                    end=validity_window.end,
                ),
            )
        )
        return cast(int, result.abi_return)

    def revoke_role(self, role: DAsaRole, address: str) -> int:
        result = self._client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(role_id=int(role), role_address=address)
        )
        return cast(int, result.abi_return)


class AccountManagerRole(_BoundRole):
    def open_account(self, *, holding_address: str, payment_address: str) -> int:
        result = self._client.send.account_open(
            AccountOpenArgs(
                holding_address=holding_address,
                payment_address=payment_address,
            )
        )
        return cast(int, result.abi_return)


class PrimaryDealerRole(_BoundRole):
    def primary_distribution(self, *, holding_address: str, units: int) -> int:
        result = self._client.send.primary_distribution(
            PrimaryDistributionArgs(holding_address=holding_address, units=units)
        )
        return cast(int, result.abi_return)


class TrusteeRole(_BoundRole):
    def set_default(self, *, defaulted: bool) -> int:
        result = self._client.send.rbac_contract_default(
            RbacContractDefaultArgs(defaulted=defaulted)
        )
        return cast(int, result.abi_return)


class AuthorityRole(_BoundRole):
    def suspend_account(self, *, holding_address: str, suspended: bool) -> int:
        result = self._client.send.account_suspension(
            AccountSuspensionArgs(holding_address=holding_address, suspended=suspended)
        )
        return cast(int, result.abi_return)

    def set_contract_suspension(self, *, suspended: bool) -> int:
        result = self._client.send.rbac_contract_suspension(
            RbacContractSuspensionArgs(suspended=suspended)
        )
        return cast(int, result.abi_return)


class ObserverRole(_BoundRole):
    def apply_non_cash_event(
        self, *, event_id: int, payload: ObservedEventRequest
    ) -> int:
        result = self._client.send.apply_non_cash_event(
            ApplyNonCashEventArgs(
                event_id=event_id,
                payload=to_client_observed_event(payload, event_id=event_id),
            )
        )
        return cast(int, result.abi_return)


class OpDaemonRole(_BoundRole):
    def fund_due_cashflows(self, *, max_event_count: int) -> FundingResult:
        result = self._client.send.fund_due_cashflows(
            FundDueCashflowsArgs(max_event_count=max_event_count)
        )
        funding = cast(CashFundingResult, result.abi_return)
        return FundingResult(
            funded_interest=funding.funded_interest,
            funded_principal=funding.funded_principal,
            total_funded=funding.total_funded,
            processed_events=funding.processed_events,
            timestamp=funding.timestamp,
        )

    def claim(
        self, *, holding_address: str, payment_info: bytes | str = b""
    ) -> ClaimResult:
        result = self._client.send.claim_due_cashflows(
            ClaimDueCashflowsArgs(
                holding_address=holding_address,
                payment_info=payment_info,
            ),
            params=CommonAppCallParams(max_fee=DEFAULT_CLAIM_FEE),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )
        claim = cast(CashClaimResult, result.abi_return)
        return ClaimResult(
            interest_amount=claim.interest_amount,
            principal_amount=claim.principal_amount,
            total_amount=claim.total_amount,
            timestamp=claim.timestamp,
            context=claim.context,
        )


class HoldingAccount(_BoundRole):
    def __init__(
        self,
        app: DAsa,
        account: SigningAccount,
        *,
        holding_address: str | None = None,
    ) -> None:
        super().__init__(app, account)
        self._holding_address = holding_address or account.address

    @property
    def holding_address(self) -> str:
        return self._holding_address

    def get_raw_position(self) -> AccountPosition:
        position = self._app.raw_client.state.box.account.get_value(
            self.holding_address
        )
        if position is None:
            raise ValueError(f"unknown holding address: {self.holding_address}")
        return to_sdk_account_position(position)

    def get_actualized_position(self, at_time: int | None = None) -> AccountPosition:
        if at_time is not None:
            self._resolve_quote_timestamp(at_time)
        return _actualize_position(
            self.get_raw_position(),
            state=self.contract.get_state(),
        )

    def get_valuation(self, at_time: int | None = None) -> AccountValuation:
        valuation_timestamp = self._resolve_quote_timestamp(at_time)
        state = self.contract.get_state()
        position = self.get_actualized_position(valuation_timestamp)
        principal_share = _share_amount(
            state.outstanding_principal,
            units=position.units,
            total_units=state.total_units,
            fixed_point_scale=state.fixed_point_scale,
        )
        accrued_interest_not_due = self._accrued_interest_not_due(
            state=state,
            units=position.units,
            at_time=valuation_timestamp,
        )
        return AccountValuation(
            valuation_timestamp=valuation_timestamp,
            position=position,
            principal_share=principal_share,
            claimable_interest=position.claimable_interest,
            claimable_principal=position.claimable_principal,
            accrued_interest_not_due=accrued_interest_not_due,
            economic_value_total=(
                principal_share
                + position.claimable_interest
                + position.claimable_principal
                + accrued_interest_not_due
            ),
        )

    def quote_trade(
        self,
        units: int,
        *,
        at_time: int | None = None,
        trade_side: Literal["buy", "sell"] = "sell",
        clean_quote: TradeQuoteInput | None = None,
    ) -> TradeQuote:
        if trade_side not in {"buy", "sell"}:
            raise ValueError("trade_side must be 'buy' or 'sell'")
        valuation_timestamp = self._resolve_quote_timestamp(at_time)
        state = self.contract.get_state()
        next_due_event = self.contract.get_next_due_event()
        if (
            next_due_event is not None
            and next_due_event.scheduled_time <= valuation_timestamp
        ):
            raise ValueError("cannot quote while a due ACTUS event is pending")
        self._assert_transfer_is_open(state=state, at_time=valuation_timestamp)

        valuation = self.get_valuation(valuation_timestamp)
        if units <= 0:
            raise ValueError("units must be greater than zero")
        if units > valuation.position.units:
            raise ValueError("units exceed the actualized active balance")

        principal_share_total = _share_amount(
            state.outstanding_principal,
            units=units,
            total_units=state.total_units,
            fixed_point_scale=state.fixed_point_scale,
        )
        accrued_interest_not_due_total = self._accrued_interest_not_due(
            state=state,
            units=units,
            at_time=valuation_timestamp,
        )
        par_reference_clean_total = principal_share_total
        par_reference_dirty_total = (
            principal_share_total + accrued_interest_not_due_total
        )

        market_clean_total: Decimal | None = None
        market_dirty_total: Decimal | None = None
        market_clean_per_unit: Decimal | None = None
        market_dirty_per_unit: Decimal | None = None
        if clean_quote is not None:
            market_clean_total = clean_quote.resolve(
                units=units,
                pricing_context=self._app.pricing_context,
            )
            market_dirty_total = market_clean_total + Decimal(
                accrued_interest_not_due_total
            )
            market_clean_per_unit = market_clean_total / Decimal(units)
            market_dirty_per_unit = market_dirty_total / Decimal(units)

        return TradeQuote(
            trade_side=trade_side,
            units=units,
            valuation_timestamp=valuation_timestamp,
            principal_share_total=principal_share_total,
            accrued_interest_not_due_total=accrued_interest_not_due_total,
            economic_value_total=par_reference_dirty_total,
            seller_retained_claimable_interest=valuation.claimable_interest,
            seller_retained_claimable_principal=valuation.claimable_principal,
            par_reference_clean_total=par_reference_clean_total,
            par_reference_dirty_total=par_reference_dirty_total,
            market_clean_total=market_clean_total,
            market_dirty_total=market_dirty_total,
            market_clean_per_unit=market_clean_per_unit,
            market_dirty_per_unit=market_dirty_per_unit,
        )

    def build_otc_dvp(
        self,
        *,
        buyer: SigningAccount,
        units: int,
        payment_amount: int,
        payment_asset_id: int | None = None,
        seller: SigningAccount | None = None,
        sender_holding_address: str | None = None,
        receiver_holding_address: str | None = None,
        payment_receiver: str | None = None,
        at_time: int | None = None,
        clean_quote: TradeQuoteInput | None = None,
        quote_tolerance: int | None = None,
    ) -> OtcDvpDraft:
        seller_account = seller or self.account
        sender_address = sender_holding_address or self.holding_address
        receiver_address = receiver_holding_address or buyer.address
        payee = payment_receiver or seller_account.address

        if units <= 0:
            raise ValueError("units must be greater than zero")
        if payment_amount <= 0:
            raise ValueError("payment_amount must be greater than zero")
        if (
            seller_account.address == buyer.address
            or sender_address == receiver_address
        ):
            raise ValueError("buyer and seller must be different")
        if seller_account.address != sender_address:
            raise ValueError(
                "seller signer must match sender_holding_address for the D-ASA transfer leg"
            )

        quote: TradeQuote | None = None
        if quote_tolerance is not None:
            quote = self.quote_trade(
                units,
                at_time=at_time,
                trade_side="sell",
                clean_quote=clean_quote,
            )
            reference_total = (
                quote.market_dirty_total
                if quote.market_dirty_total is not None
                else Decimal(quote.par_reference_dirty_total)
            )
            delta = abs(Decimal(payment_amount) - reference_total)
            if delta > Decimal(quote_tolerance):
                raise ValueError(
                    "payment amount is outside the configured quote tolerance"
                )

        seller_client = self._app.raw_client.clone(
            default_sender=seller_account.address,
            default_signer=seller_account.signer,
        )
        if payment_asset_id is None:
            payment_transaction = seller_client.algorand.create_transaction.payment(
                PaymentParams(
                    sender=buyer.address,
                    signer=buyer.signer,
                    receiver=payee,
                    amount=AlgoAmount.from_micro_algo(payment_amount),
                )
            )
        else:
            payment_transaction = (
                seller_client.algorand.create_transaction.asset_transfer(
                    AssetTransferParams(
                        asset_id=payment_asset_id,
                        amount=payment_amount,
                        sender=buyer.address,
                        signer=buyer.signer,
                        receiver=payee,
                    )
                )
            )

        composer = (
            seller_client.new_group()
            .add_transaction(
                payment_transaction,
                buyer.signer,
            )
            .transfer(
                TransferArgs(
                    sender_holding_address=sender_address,
                    receiver_holding_address=receiver_address,
                    units=units,
                )
            )
        )
        return OtcDvpDraft(
            buyer_address=buyer.address,
            seller_address=seller_account.address,
            sender_holding_address=sender_address,
            receiver_holding_address=receiver_address,
            units=units,
            payment_amount=payment_amount,
            payment_asset_id=payment_asset_id,
            payment_transaction=payment_transaction,
            quote=quote,
            composer=composer,
        )

    def transfer(self, *, receiver_holding_address: str, units: int) -> int:
        if self.account.address != self.holding_address:
            raise ValueError(
                "transfer requires a signer that matches the holding address"
            )
        result = self._client.send.transfer(
            TransferArgs(
                sender_holding_address=self.holding_address,
                receiver_holding_address=receiver_holding_address,
                units=units,
            )
        )
        return cast(int, result.abi_return)

    def claim(self, *, payment_info: bytes | str = b"") -> ClaimResult:
        result = self._client.send.claim_due_cashflows(
            ClaimDueCashflowsArgs(
                holding_address=self.holding_address,
                payment_info=payment_info,
            ),
            params=CommonAppCallParams(max_fee=DEFAULT_CLAIM_FEE),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )
        claim = cast(CashClaimResult, result.abi_return)
        return ClaimResult(
            interest_amount=claim.interest_amount,
            principal_amount=claim.principal_amount,
            total_amount=claim.total_amount,
            timestamp=claim.timestamp,
            context=claim.context,
        )

    def update_payment_address(self, *, payment_address: str) -> int:
        if self.account.address != self.holding_address:
            raise ValueError(
                "payment address updates require a signer that matches the holding address"
            )
        result = self._client.send.account_update_payment_address(
            AccountUpdatePaymentAddressArgs(
                holding_address=self.holding_address,
                payment_address=payment_address,
            )
        )
        return cast(int, result.abi_return)

    def _resolve_quote_timestamp(self, at_time: int | None) -> int:
        now = _latest_timestamp(self._app.raw_client)
        if at_time is None:
            return now
        if at_time < now:
            raise ValueError(
                "at_time cannot be earlier than the latest on-chain timestamp"
            )
        return at_time

    def _assert_transfer_is_open(self, *, state: ContractState, at_time: int) -> None:
        if state.status == enums.STATUS_PENDING_IED:
            raise ValueError("cannot quote or trade before IED executes")
        if state.transfer_opening_date and at_time < state.transfer_opening_date:
            raise ValueError("transfer window is not open yet")
        if state.transfer_closure_date and at_time >= state.transfer_closure_date:
            raise ValueError("transfer window is closed")

    def _accrued_interest_not_due(
        self,
        *,
        state: ContractState,
        units: int,
        at_time: int,
    ) -> int:
        if state.status != enums.STATUS_ACTIVE or units == 0:
            return 0
        if state.total_units <= 0 or state.fixed_point_scale <= 0:
            return 0

        accrued_share = _share_amount(
            state.accrued_interest,
            units=units,
            total_units=state.total_units,
            fixed_point_scale=state.fixed_point_scale,
        )
        if state.event_cursor >= state.schedule_entry_count:
            return accrued_share

        next_entry = self.contract.get_schedule_entry(state.event_cursor)
        if next_entry is None or at_time >= next_entry.scheduled_time:
            return accrued_share
        start_time = self._partial_accrual_start(state=state)
        if start_time is None or at_time <= start_time:
            return accrued_share

        partial_factor = year_fraction_fixed(
            start_time,
            at_time,
            day_count_convention=state.day_count_convention,
            maturity_date=state.maturity_date or None,
        )
        if partial_factor == 0:
            return accrued_share

        period_interest = _scaled_mul_div(
            state.interest_calculation_base,
            state.nominal_interest_rate,
            state.fixed_point_scale,
        )
        partial_amount = _scaled_mul_div(
            period_interest,
            partial_factor,
            state.fixed_point_scale,
        )
        return accrued_share + _share_amount(
            partial_amount,
            units=units,
            total_units=state.total_units,
            fixed_point_scale=state.fixed_point_scale,
        )

    def _partial_accrual_start(self, *, state: ContractState) -> int | None:
        if state.event_cursor == 0:
            return None
        previous_entry = self.contract.get_schedule_entry(state.event_cursor - 1)
        if previous_entry is None:
            return None
        return previous_entry.scheduled_time


class DAsa:
    def __init__(
        self,
        client: _GeneratedDasaClient,
        *,
        pricing_context: PricingContext | None = None,
    ) -> None:
        self._client = client
        self._pricing_context = pricing_context
        self.contract = ContractView(client, pricing_context=pricing_context)

    @classmethod
    def deploy(
        cls,
        *,
        algorand: AlgorandClient,
        arranger: SigningAccount,
        app_name: str | None = None,
        send_params: SendParams | None = None,
    ) -> DAsa:
        factory = _GeneratedDasaFactory(
            algorand,
            app_name=app_name,
            default_sender=arranger.address,
            default_signer=arranger.signer,
        )
        client, _ = factory.send.create.contract_create(
            ContractCreateArgs(arranger=arranger.address),
            send_params=send_params,
        )
        return cls(client)

    @classmethod
    def deploy_configured(
        cls,
        *,
        algorand: AlgorandClient,
        arranger: SigningAccount,
        normalized: NormalizationResult | None = None,
        contract: ContractAttributes | None = None,
        denomination_asset_id: int | None = None,
        denomination_asset_decimals: int | None = None,
        notional_unit_value: int | float | Decimal | None = None,
        secondary_market_opening_date: int | None = None,
        secondary_market_closure_date: int | None = None,
        preprocessed_events: (
            Sequence[ObservedEventRequest | ExecutionScheduleEntry] | None
        ) = None,
        app_name: str | None = None,
        prospectus_url: str = "",
        prospectus_hash: bytes | None = None,
        page_size: int = cst.SCHEDULE_PAGE_SIZE,
        transfer_opening_date: int | None = None,
        transfer_closure_date: int | None = None,
        app_account_funding: AlgoAmount | None = DEFAULT_APP_FUNDING,
        funding_account: SigningAccount | None = None,
    ) -> DAsa:
        resolved = _normalize_result(
            normalized=normalized,
            contract=contract,
            denomination_asset_id=denomination_asset_id,
            denomination_asset_decimals=denomination_asset_decimals,
            notional_unit_value=notional_unit_value,
            secondary_market_opening_date=secondary_market_opening_date,
            secondary_market_closure_date=secondary_market_closure_date,
            preprocessed_events=preprocessed_events,
        )
        app = cls.deploy(
            algorand=algorand,
            arranger=arranger,
            app_name=app_name,
        )
        if app_account_funding is not None:
            app._fund_app_account(
                payer=funding_account or arranger,
                amount=app_account_funding,
            )
        app.arranger(arranger).configure_contract(
            normalized=resolved,
            prospectus_url=prospectus_url,
            prospectus_hash=prospectus_hash,
            page_size=page_size,
            transfer_opening_date=transfer_opening_date,
            transfer_closure_date=transfer_closure_date,
        )
        app._pricing_context = PricingContext(
            notional_unit_value=resolved.terms.notional_unit_value
        )
        app.contract._pricing_context = app._pricing_context
        return app

    @classmethod
    def from_app_id(
        cls,
        *,
        algorand: AlgorandClient,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        pricing_context: PricingContext | None = None,
    ) -> DAsa:
        return cls(
            _GeneratedDasaClient(
                algorand=algorand,
                app_id=app_id,
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
            ),
            pricing_context=pricing_context,
        )

    @classmethod
    def from_client(
        cls,
        client: _GeneratedDasaClient,
        *,
        pricing_context: PricingContext | None = None,
    ) -> DAsa:
        return cls(client, pricing_context=pricing_context)

    @property
    def raw_client(self) -> _GeneratedDasaClient:
        return self._client

    @property
    def pricing_context(self) -> PricingContext | None:
        return self._pricing_context

    @property
    def app_id(self) -> int:
        return self._client.app_id

    @property
    def app_address(self) -> str:
        return self._client.app_address

    def arranger(self, account: SigningAccount) -> ArrangerRole:
        return ArrangerRole(self, account)

    def account(
        self,
        holding_account: SigningAccount,
        holding_address: str | None = None,
    ) -> HoldingAccount:
        return HoldingAccount(self, holding_account, holding_address=holding_address)

    def account_manager(self, account: SigningAccount) -> AccountManagerRole:
        return AccountManagerRole(self, account)

    def primary_dealer(self, account: SigningAccount) -> PrimaryDealerRole:
        return PrimaryDealerRole(self, account)

    def trustee(self, account: SigningAccount) -> TrusteeRole:
        return TrusteeRole(self, account)

    def authority(self, account: SigningAccount) -> AuthorityRole:
        return AuthorityRole(self, account)

    def observer(self, account: SigningAccount) -> ObserverRole:
        return ObserverRole(self, account)

    def op_daemon(self, account: SigningAccount) -> OpDaemonRole:
        return OpDaemonRole(self, account)

    def _fund_app_account(self, *, payer: SigningAccount, amount: AlgoAmount) -> None:
        self._client.algorand.send.payment(
            PaymentParams(
                sender=payer.address,
                signer=payer.signer,
                receiver=self.app_address,
                amount=amount,
            )
        )
