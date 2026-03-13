from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AssetOptInParams,
    AssetTransferParams,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts import constants as cst
from smart_contracts import enums
from src import ExecutionScheduleEntry, NormalizationResult
from src.artifacts.dasa_client import (
    AccountOpenArgs,
    ContractConfigArgs,
    ContractScheduleArgs,
    DasaClient,
    InitialKernelState,
    NormalizedActusTerms,
    PrimaryDistributionArgs,
    Prospectus,
)
from src.localnet import Currency, DAsaAccountManager, DAsaPrimaryDealer
from src.registry import EVENT_TYPE_IDS
from src.schedule import Cycle

PRINCIPAL = 10_000
MINIMUM_DENOMINATION = 100
ISSUANCE_DELAY_CYCLE = Cycle.parse_cycle("30D")
LOCALNET_EXPLORER_TX_BASE_URL = "https://lora.algokit.io/localnet/transaction/"
EVENT_TYPE_NAMES = {value: key for key, value in EVENT_TYPE_IDS.items()}
STATUS_NAMES = {
    enums.STATUS_INACTIVE: "INACTIVE",
    enums.STATUS_PENDING_IED: "PENDING_IED",
    enums.STATUS_ACTIVE: "ACTIVE",
    enums.STATUS_ENDED: "ENDED",
}


@dataclass(frozen=True)
class PamLifecycleParticipants:
    investor: SigningAccount
    receiver: SigningAccount


@dataclass(frozen=True, slots=True)
class PamLifecycleClaimTrace:
    interest_amount: int
    principal_amount: int
    total_amount: int
    timestamp: int


@dataclass(frozen=True, slots=True)
class PamLifecycleTraceStep:
    schedule_entry: ExecutionScheduleEntry
    execution_event: dict[str, int]
    funded_amount: int
    execution_tx_id: str
    claim: PamLifecycleClaimTrace | None = None
    claim_tx_id: str | None = None


@dataclass(frozen=True, slots=True)
class PamLifecycleTrace:
    title: str
    contract_variant: str
    description: str
    normalized: NormalizationResult
    currency_decimals: int
    currency_unit_name: str
    investor_payment_amount: int
    total_interest_claimed: int
    total_principal_claimed: int
    status_before_ied: int
    status_after_ied: int
    final_status: int
    steps: tuple[PamLifecycleTraceStep, ...]


def client_terms(result: NormalizationResult) -> NormalizedActusTerms:
    return NormalizedActusTerms(
        contract_type=result.terms.contract_type,
        denomination_asset_id=result.terms.denomination_asset_id,
        settlement_asset_id=result.terms.denomination_asset_id,
        total_units=result.terms.total_units,
        notional_principal=result.terms.notional_principal,
        initial_exchange_amount=result.terms.initial_exchange_amount,
        initial_exchange_date=result.terms.initial_exchange_date,
        maturity_date=result.terms.maturity_date or 0,
        day_count_convention=int(result.terms.day_count_convention),
        rate_reset_spread=result.terms.rate_reset_spread,
        rate_reset_multiplier=result.terms.rate_reset_multiplier,
        rate_reset_floor=result.terms.rate_reset_floor,
        rate_reset_cap=result.terms.rate_reset_cap,
        rate_reset_next=result.terms.rate_reset_next,
        has_rate_reset_floor=result.terms.has_rate_reset_floor,
        has_rate_reset_cap=result.terms.has_rate_reset_cap,
        dynamic_principal_redemption=result.terms.dynamic_principal_redemption,
        fixed_point_scale=result.terms.fixed_point_scale,
    )


def client_initial_state(result: NormalizationResult) -> InitialKernelState:
    return InitialKernelState(
        status_date=result.initial_state.status_date,
        event_cursor=result.initial_state.event_cursor,
        outstanding_principal=result.initial_state.outstanding_principal,
        interest_calculation_base=result.initial_state.interest_calculation_base,
        nominal_interest_rate=result.initial_state.nominal_interest_rate,
        accrued_interest=result.initial_state.accrued_interest,
        next_principal_redemption=result.initial_state.next_principal_redemption,
        cumulative_interest_index=result.initial_state.cumulative_interest_index,
        cumulative_principal_index=result.initial_state.cumulative_principal_index,
    )


def client_schedule_page(
    page: tuple[ExecutionScheduleEntry, ...],
) -> list[tuple[int, int, int, int, int, int, int, int, int]]:
    return [
        (
            entry.event_id,
            EVENT_TYPE_IDS[entry.event_type],
            entry.scheduled_time,
            entry.accrual_factor,
            entry.redemption_accrual_factor,
            entry.next_nominal_interest_rate,
            entry.next_principal_redemption,
            entry.next_outstanding_principal,
            entry.flags,
        )
        for entry in page
    ]


def cycle_duration_seconds(cycle: Cycle) -> int:
    if cycle.unit == "D":
        return cycle.count * cst.DAY_2_SEC
    if cycle.unit == "W":
        return cycle.count * 7 * cst.DAY_2_SEC
    raise ValueError(f"Unsupported fixed-duration ACTUS cycle for this test: {cycle}")


def scale_currency_amount(amount: int, currency_scale: int) -> int:
    return amount * currency_scale


def make_claim_trace(
    *,
    interest_amount: int,
    principal_amount: int,
    total_amount: int,
    timestamp: int,
) -> PamLifecycleClaimTrace:
    return PamLifecycleClaimTrace(
        interest_amount=interest_amount,
        principal_amount=principal_amount,
        total_amount=total_amount,
        timestamp=timestamp,
    )


def format_lifecycle_trace(trace: PamLifecycleTrace) -> str:
    total_received = trace.total_interest_claimed + trace.total_principal_claimed
    net_cash = total_received - trace.investor_payment_amount
    principal = _format_asset_amount(
        trace.normalized.terms.notional_principal,
        decimals=trace.currency_decimals,
        unit_name=trace.currency_unit_name,
    )
    issue_price = _format_asset_amount(
        trace.investor_payment_amount,
        decimals=trace.currency_decimals,
        unit_name=trace.currency_unit_name,
    )
    interest_total = _format_asset_amount(
        trace.total_interest_claimed,
        decimals=trace.currency_decimals,
        unit_name=trace.currency_unit_name,
    )
    principal_total = _format_asset_amount(
        trace.total_principal_claimed,
        decimals=trace.currency_decimals,
        unit_name=trace.currency_unit_name,
    )
    total_received_label = _format_asset_amount(
        total_received,
        decimals=trace.currency_decimals,
        unit_name=trace.currency_unit_name,
    )
    net_cash_label = _format_asset_amount(
        net_cash,
        decimals=trace.currency_decimals,
        unit_name=trace.currency_unit_name,
    )
    maturity_label = (
        _format_timestamp(trace.normalized.terms.maturity_date)
        if trace.normalized.terms.maturity_date
        else "open-ended"
    )

    lines = [
        trace.title,
        "=" * len(trace.title),
        f"Variant      : {trace.contract_variant}",
        f"Description  : {trace.description}",
        f"Units        : {trace.normalized.terms.total_units}",
        f"Principal    : {principal}",
        f"Issue price  : {issue_price}",
        f"Issue date   : {_format_timestamp(trace.normalized.terms.initial_exchange_date)}",
        f"Maturity     : {maturity_label}",
        (
            "Status path  : "
            f"{STATUS_NAMES[trace.status_before_ied]} -> "
            f"{STATUS_NAMES[trace.status_after_ied]} -> "
            f"{STATUS_NAMES[trace.final_status]}"
        ),
        (
            "Investor P&L : "
            f"paid {issue_price}, received {total_received_label} "
            f"(interest {interest_total}, principal {principal_total}), net {net_cash_label}"
        ),
        f"Timeline ({trace.currency_unit_name} amounts)",
        "--------------------------------",
    ]

    table_headers = (
        "id",
        "evt",
        "due",
        "applied",
        "lag",
        "accrual",
        "payoff",
        "settled",
        "interest",
        "principal",
        "next out",
        "rate",
    )
    table_rows: list[tuple[str, ...]] = []

    for step in trace.steps:
        proof = step.execution_event
        proof_type = EVENT_TYPE_NAMES.get(proof["event_type"], str(proof["event_type"]))
        table_rows.append(
            (
                f"{step.schedule_entry.event_id:02d}",
                proof_type,
                _format_table_timestamp(step.schedule_entry.scheduled_time),
                _format_table_timestamp(proof["applied_at"]),
                _format_time_delta(
                    proof["applied_at"] - step.schedule_entry.scheduled_time
                ),
                _format_ratio(step.schedule_entry.accrual_factor),
                _format_scaled_amount(
                    proof["payoff"],
                    decimals=trace.currency_decimals,
                ),
                _format_scaled_amount(
                    proof["settled_amount"],
                    decimals=trace.currency_decimals,
                ),
                (
                    _format_scaled_amount(
                        step.claim.interest_amount,
                        decimals=trace.currency_decimals,
                    )
                    if step.claim is not None
                    else "-"
                ),
                (
                    _format_scaled_amount(
                        step.claim.principal_amount,
                        decimals=trace.currency_decimals,
                    )
                    if step.claim is not None
                    else "-"
                ),
                _format_scaled_amount(
                    step.schedule_entry.next_outstanding_principal,
                    decimals=trace.currency_decimals,
                ),
                (
                    _format_rate(step.schedule_entry.next_nominal_interest_rate)
                    if step.schedule_entry.next_nominal_interest_rate
                    else "-"
                ),
            )
        )

    lines.extend(_render_table(table_headers, table_rows))
    lines.extend(["", "Execution Links", "---------------"])
    execution_link_headers = ("id", "evt", "execution", "claim")
    execution_link_rows = [
        (
            f"{step.schedule_entry.event_id:02d}",
            step.schedule_entry.event_type,
            _format_explorer_transaction_url(step.execution_tx_id),
            (
                _format_explorer_transaction_url(step.claim_tx_id)
                if step.claim_tx_id is not None
                else "-"
            ),
        )
        for step in trace.steps
    ]
    lines.extend(_render_table(execution_link_headers, execution_link_rows))
    return "\n".join(lines)


def _open_contract_account(
    client: DasaClient,
    *,
    account_manager: SigningAccount,
    holding_address: str,
    payment_address: str,
) -> None:
    client.send.account_open(
        AccountOpenArgs(
            holding_address=holding_address,
            payment_address=payment_address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
            signer=account_manager.signer,
        ),
    )


def setup_pam_lifecycle(
    *,
    client: DasaClient,
    primary_dealer: DAsaPrimaryDealer,
    account_manager: DAsaAccountManager,
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: Currency,
    normalized: NormalizationResult,
    bank_funding_amount: int,
    investor_payment_amount: int,
    prospectus_url: str,
) -> PamLifecycleParticipants:
    pages = normalized.schedule_pages(cst.SCHEDULE_PAGE_SIZE)
    client.send.contract_config(
        ContractConfigArgs(
            terms=client_terms(normalized),
            initial_state=client_initial_state(normalized),
            prospectus=Prospectus(
                hash=bytes(32),
                url=prospectus_url,
            ),
        ),
        params=CommonAppCallParams(max_fee=AlgoAmount.from_micro_algo(5_000)),
        send_params=SendParams(cover_app_call_inner_transaction_fees=True),
    )
    for index, page in enumerate(pages):
        client.send.contract_schedule(
            ContractScheduleArgs(
                schedule_page_index=index,
                is_last_page=index == len(pages) - 1,
                schedule_page=client_schedule_page(page),
            ),
            params=CommonAppCallParams(max_fee=AlgoAmount.from_micro_algo(5_000)),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )

    if bank_funding_amount > 0:
        algorand.send.asset_transfer(
            AssetTransferParams(
                asset_id=currency.id,
                amount=bank_funding_amount,
                receiver=client.app_address,
                sender=bank.address,
                signer=bank.signer,
            )
        )

    investor = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=investor.address,
        min_spending_balance=AlgoAmount.from_algo(10),
    )
    algorand.send.asset_opt_in(
        AssetOptInParams(
            asset_id=currency.id,
            sender=investor.address,
            signer=investor.signer,
        )
    )
    _open_contract_account(
        client,
        account_manager=account_manager,
        holding_address=investor.address,
        payment_address=investor.address,
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            asset_id=currency.id,
            amount=investor_payment_amount,
            receiver=investor.address,
            sender=bank.address,
            signer=bank.signer,
        )
    )

    receiver = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=receiver.address,
        min_spending_balance=AlgoAmount.from_algo(10),
    )
    _open_contract_account(
        client,
        account_manager=account_manager,
        holding_address=receiver.address,
        payment_address=receiver.address,
    )

    assert (
        algorand.asset.get_account_information(investor.address, currency.id).balance
        == investor_payment_amount
    )

    investor_purchase_txn = algorand.create_transaction.asset_transfer(
        AssetTransferParams(
            asset_id=currency.id,
            amount=investor_payment_amount,
            receiver=client.app_address,
            sender=investor.address,
            signer=investor.signer,
        )
    )
    client.new_group().add_transaction(
        investor_purchase_txn, investor.signer
    ).primary_distribution(
        PrimaryDistributionArgs(
            holding_address=investor.address,
            units=normalized.terms.total_units,
        ),
        params=CommonAppCallParams(
            sender=primary_dealer.address,
            signer=primary_dealer.signer,
        ),
    ).send()

    assert (
        algorand.asset.get_account_information(investor.address, currency.id).balance
        == 0
    )
    assert (
        algorand.asset.get_account_information(client.app_address, currency.id).balance
        == bank_funding_amount + investor_payment_amount
    )

    return PamLifecycleParticipants(
        investor=investor,
        receiver=receiver,
    )


def _format_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M:%SZ")


def _format_asset_amount(amount: int, *, decimals: int, unit_name: str) -> str:
    quantizer = Decimal(1).scaleb(-decimals)
    scaled = (Decimal(amount) / (Decimal(10) ** decimals)).quantize(quantizer)
    return f"{scaled:,.{decimals}f} {unit_name}"


def _format_scaled_amount(amount: int, *, decimals: int) -> str:
    quantizer = Decimal(1).scaleb(-decimals)
    scaled = (Decimal(amount) / (Decimal(10) ** decimals)).quantize(quantizer)
    return f"{scaled:,.{decimals}f}"


def _format_table_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d")


def _format_time_delta(delta_seconds: int) -> str:
    sign = "+" if delta_seconds >= 0 else "-"
    abs_delta = abs(delta_seconds)
    if abs_delta % cst.DAY_2_SEC == 0:
        return f"{sign}{abs_delta // cst.DAY_2_SEC}d"
    if abs_delta % 3600 == 0:
        return f"{sign}{abs_delta // 3600}h"
    if abs_delta % 60 == 0:
        return f"{sign}{abs_delta // 60}m"
    return f"{sign}{abs_delta}s"


def _format_ratio(value: int) -> str:
    scaled = Decimal(value) / Decimal(cst.FIXED_POINT_SCALE)
    return f"{scaled:.6f}"


def _format_rate(value: int) -> str:
    percent = Decimal(value) * Decimal(100) / Decimal(cst.FIXED_POINT_SCALE)
    return f"{percent:.4f}%"


def _format_explorer_transaction_url(tx_id: str) -> str:
    return f"{LOCALNET_EXPLORER_TX_BASE_URL}{tx_id}"


def _render_table(
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    left_align = {1, 2, 3}

    def render_row(row: tuple[str, ...]) -> str:
        cells: list[str] = []
        for index, cell in enumerate(row):
            if index in left_align:
                cells.append(cell.ljust(widths[index]))
            else:
                cells.append(cell.rjust(widths[index]))
        return " | ".join(cells)

    separator = "-+-".join("-" * width for width in widths)
    return [render_row(headers), separator, *[render_row(row) for row in rows]]
