from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AssetCreateParams,
    AssetOptInParams,
    SigningAccount,
)

from d_asa import NormalizationResult
from d_asa.localnet import (
    Currency,
    algorand_client_from_localnet,
    load_localnet_config,
    wait_for_localnet,
)

DEFAULT_CURRENCY_NAME = "Euro"
DEFAULT_CURRENCY_UNIT = "EUR"
DEFAULT_CURRENCY_DECIMALS = 2
DEFAULT_CURRENCY_TOTAL_UNITS = 10_000_000


def connect_localnet(*, timeout_seconds: float = 30.0) -> AlgorandClient:
    localnet_config = load_localnet_config(default_host="localhost")
    wait_for_localnet(
        localnet_config=localnet_config,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=1.0,
    )
    return algorand_client_from_localnet(localnet_config)


def create_funded_account(
    algorand: AlgorandClient,
    *,
    min_algo: int = 20,
) -> SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=AlgoAmount.from_algo(min_algo),
    )
    return account


def create_currency(
    algorand: AlgorandClient,
    *,
    issuer: SigningAccount,
    asset_name: str = DEFAULT_CURRENCY_NAME,
    unit_name: str = DEFAULT_CURRENCY_UNIT,
    decimals: int = DEFAULT_CURRENCY_DECIMALS,
    total_units: int = DEFAULT_CURRENCY_TOTAL_UNITS,
) -> Currency:
    total = total_units * (10**decimals)
    currency_id = algorand.send.asset_create(
        AssetCreateParams(
            sender=issuer.address,
            signer=issuer.signer,
            total=total,
            decimals=decimals,
            asset_name=asset_name,
            unit_name=unit_name,
        )
    ).asset_id
    return Currency(
        id=currency_id,
        total=total,
        decimals=decimals,
        name=asset_name,
        unit_name=unit_name,
        asa_to_unit=1 / (10**decimals),
    )


def opt_in_asset(
    algorand: AlgorandClient,
    *,
    account: SigningAccount,
    asset_id: int,
) -> None:
    algorand.send.asset_opt_in(
        AssetOptInParams(
            asset_id=asset_id,
            sender=account.address,
            signer=account.signer,
        )
    )


def format_asset_amount(
    amount: int,
    *,
    decimals: int,
    unit_name: str | None = None,
) -> str:
    quantizer = Decimal(1).scaleb(-decimals)
    scaled = (Decimal(amount) / (Decimal(10) ** decimals)).quantize(quantizer)
    if unit_name is None:
        return f"{scaled:,.{decimals}f}"
    return f"{scaled:,.{decimals}f} {unit_name}"


def format_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M:%SZ")


def format_rate(value: int, *, fixed_point_scale: int) -> str:
    rate_percent = Decimal(value) * Decimal(100) / Decimal(fixed_point_scale)
    return f"{rate_percent:.4f}%"


def schedule_rows(
    normalized: NormalizationResult,
    *,
    currency_decimals: int,
) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for entry in normalized.schedule:
        rows.append(
            {
                "event_id": entry.event_id,
                "event_type": entry.event_type,
                "scheduled_time": format_timestamp(entry.scheduled_time),
                "accrual_factor": f"{Decimal(entry.accrual_factor) / Decimal(normalized.terms.fixed_point_scale):.6f}",
                "next_outstanding_principal": format_asset_amount(
                    entry.next_outstanding_principal,
                    decimals=currency_decimals,
                ),
                "next_nominal_interest_rate": (
                    format_rate(
                        entry.next_nominal_interest_rate,
                        fixed_point_scale=normalized.terms.fixed_point_scale,
                    )
                    if entry.next_nominal_interest_rate is not None
                    else "-"
                ),
            }
        )
    return rows


def cashflow_rows(
    cashflows: Sequence[Mapping[str, Any]],
    *,
    currency: Currency,
) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for cashflow in cashflows:
        rows.append(
            {
                "event_id": int(cashflow["event_id"]),
                "event_type": str(cashflow["event_type"]),
                "scheduled_time": format_timestamp(int(cashflow["scheduled_time"])),
                "funded": format_asset_amount(
                    int(cashflow["funded"]),
                    decimals=currency.decimals,
                    unit_name=currency.unit_name,
                ),
                "interest_claimed": format_asset_amount(
                    int(cashflow["interest_claimed"]),
                    decimals=currency.decimals,
                    unit_name=currency.unit_name,
                ),
                "principal_claimed": format_asset_amount(
                    int(cashflow["principal_claimed"]),
                    decimals=currency.decimals,
                    unit_name=currency.unit_name,
                ),
                "total_claimed": format_asset_amount(
                    int(cashflow["total_claimed"]),
                    decimals=currency.decimals,
                    unit_name=currency.unit_name,
                ),
                "claim_timestamp": format_timestamp(int(cashflow["claim_timestamp"])),
            }
        )
    return rows


def render_table(rows: Sequence[Mapping[str, object]]) -> str:
    if not rows:
        return "(no rows)"

    headers = list(rows[0].keys())
    widths = [len(header) for header in headers]
    rendered_rows: list[list[str]] = []
    for row in rows:
        rendered = [str(row[header]) for header in headers]
        rendered_rows.append(rendered)
        widths = [
            max(current_width, len(value))
            for current_width, value in zip(widths, rendered, strict=True)
        ]

    header_line = " | ".join(
        header.ljust(width) for header, width in zip(headers, widths, strict=True)
    )
    divider_line = "-+-".join("-" * width for width in widths)
    row_lines = [
        " | ".join(value.ljust(width) for value, width in zip(row, widths, strict=True))
        for row in rendered_rows
    ]
    return "\n".join([header_line, divider_line, *row_lines])
