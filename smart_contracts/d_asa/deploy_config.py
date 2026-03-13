from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

import algokit_utils
from algokit_utils import (
    AlgoAmount,
    AssetCreateParams,
    CommonAppCallParams,
    PaymentParams,
    SendParams,
    SigningAccount,
)
from algosdk.constants import ZERO_ADDRESS

from src.d_asa import (
    ExecutionScheduleEntry,
    NormalizationResult,
    normalize_contract_attributes,
)
from src.d_asa.artifacts.dasa_client import (
    ContractConfigArgs,
    ContractCreateArgs,
    ContractScheduleArgs,
    DasaClient,
    DasaFactory,
    DasaMethodCallCreateParams,
    InitialKernelState,
    NormalizedActusTerms,
    Prospectus,
)
from src.d_asa.contracts import (
    make_pam_fixed_coupon_bond_profile,
    make_pam_zero_coupon_bond,
)
from src.d_asa.schedule import Cycle
from smart_contracts import constants as cst
from smart_contracts import enums

logger = logging.getLogger(__name__)

AlgodStatus = Mapping[str, int]
AlgodBlock = Mapping[str, int]
AlgodBlockInfo = Mapping[str, object]

DEMO_APP_FUNDING_ALGO = 2
DEMO_ASSET_DECIMALS = 2
DEMO_ASSET_NAME = "D-ASA Demo Euro"
DEMO_ASSET_TOTAL = 10_000_000
DEMO_ASSET_UNIT_NAME = "€"
DEMO_FCB_APP_NAME = "dasa-demo-fcb"
DEMO_FCB_NOMINAL_RATE = 0.02
DEMO_FCB_PROSPECTUS_URL = "D-ASA demo fixed coupon bond"
DEMO_FIXED_COUPON_MATURITY_CYCLE = Cycle.parse_cycle("1800D")
DEMO_FIXED_COUPON_PAYMENT_CYCLE = Cycle.parse_cycle("90D")
DEMO_ISSUANCE_DELAY_CYCLE = Cycle.parse_cycle("30D")
DEMO_NOTIONAL_PRINCIPAL = 10_000
DEMO_NOTIONAL_UNIT_VALUE = 100
DEMO_ZCB_APP_NAME = "dasa-demo-zcb"
DEMO_ZCB_DISCOUNT_BPS = 200
DEMO_ZCB_MATURITY_CYCLE = Cycle.parse_cycle("360D")
DEMO_ZCB_PROSPECTUS_URL = "D-ASA demo zero coupon bond"


@dataclass(frozen=True, slots=True)
class DenominationAsset:
    asset_id: int
    decimals: int


@dataclass(frozen=True, slots=True)
class DemoDeploymentContext:
    current_ts: int
    denomination_asset: DenominationAsset


@dataclass(frozen=True, slots=True)
class DemoInstrumentSpec:
    label: str
    prospectus_url: str
    normalized: NormalizationResult


def _get_arranger_account(
    *,
    algorand: algokit_utils.AlgorandClient,
    deployer: SigningAccount,
) -> SigningAccount:
    arranger_address = os.getenv("ARRANGER_ADDRESS")
    arranger: SigningAccount | None = None

    try:
        arranger = algorand.account.from_environment("ARRANGER")
    except Exception:  # pragma: no cover - environment-driven branch
        arranger = None

    if arranger_address and arranger_address != ZERO_ADDRESS:
        if arranger is not None:
            if arranger.address != arranger_address:
                raise ValueError(
                    "ARRANGER account signer does not match ARRANGER_ADDRESS"
                )
            return arranger
        if arranger_address == deployer.address:
            logger.info("ARRANGER_ADDRESS matches DEPLOYER; using deployer signer")
            return deployer
        raise ValueError(
            "ARRANGER_ADDRESS is set but no ARRANGER signer is configured. "
            "Set ARRANGER credentials or unset ARRANGER_ADDRESS to use DEPLOYER."
        )

    if arranger is not None:
        logger.info("Using ARRANGER signer from environment")
        return arranger

    logger.info("ARRANGER is unset; defaulting arranger to DEPLOYER")
    return deployer


def _cycle_duration_seconds(cycle: Cycle) -> int:
    if cycle.unit == "D":
        return cycle.count * cst.DAY_2_SEC
    if cycle.unit == "W":
        return cycle.count * 7 * cst.DAY_2_SEC
    raise ValueError(f"Unsupported fixed-duration ACTUS cycle: {cycle}")


def _get_latest_timestamp(algorand: algokit_utils.AlgorandClient) -> int:
    algod_client = algorand.client.algod
    status = cast(AlgodStatus, algod_client.status())
    last_round = status["last-round"]
    block_info = cast(AlgodBlockInfo, algod_client.block_info(last_round))
    block = cast(AlgodBlock, block_info["block"])
    return block["ts"]


def _resolve_denomination_asset(
    *,
    algorand: algokit_utils.AlgorandClient,
    issuer: SigningAccount,
) -> DenominationAsset:
    denomination_asset_id = os.getenv("DENOMINATION_ASSET_ID")
    if denomination_asset_id:
        asset = algorand.asset.get_by_id(int(denomination_asset_id))
        logger.info(
            "Using existing denomination asset %s (%s)",
            asset.asset_id,
            asset.unit_name or "unknown unit",
        )
        return DenominationAsset(asset_id=asset.asset_id, decimals=asset.decimals)

    decimals: int = int(
        os.getenv("DENOMINATION_ASSET_DECIMALS", str(DEMO_ASSET_DECIMALS))
    )
    asset_total: int = int(os.getenv("DENOMINATION_ASSET_TOTAL", str(DEMO_ASSET_TOTAL)))
    scale: int = 10**decimals
    total: int = asset_total * scale
    asset_name: str = os.getenv("DENOMINATION_ASSET_NAME", DEMO_ASSET_NAME)
    unit_name: str = os.getenv("DENOMINATION_ASSET_UNIT_NAME", DEMO_ASSET_UNIT_NAME)

    asset_id = algorand.send.asset_create(
        AssetCreateParams(
            sender=issuer.address,
            signer=issuer.signer,
            total=total,
            decimals=decimals,
            asset_name=asset_name,
            unit_name=unit_name,
        )
    ).asset_id
    logger.info("Created denomination asset %s (%s)", asset_id, unit_name)
    return DenominationAsset(asset_id=asset_id, decimals=decimals)


def _get_demo_context(
    *,
    algorand: algokit_utils.AlgorandClient,
    deployer: SigningAccount,
) -> DemoDeploymentContext:
    return DemoDeploymentContext(
        current_ts=_get_latest_timestamp(algorand),
        denomination_asset=_resolve_denomination_asset(
            algorand=algorand,
            issuer=deployer,
        ),
    )


def build_fixed_coupon_bond_demo(context: DemoDeploymentContext) -> DemoInstrumentSpec:
    issuance_delay = _cycle_duration_seconds(DEMO_ISSUANCE_DELAY_CYCLE)
    coupon_period = _cycle_duration_seconds(DEMO_FIXED_COUPON_PAYMENT_CYCLE)
    issuance_date = context.current_ts + issuance_delay
    maturity_date = issuance_date + _cycle_duration_seconds(
        DEMO_FIXED_COUPON_MATURITY_CYCLE
    )
    first_coupon_date = issuance_date + coupon_period

    attrs = make_pam_fixed_coupon_bond_profile(
        contract_id=1,
        status_date=context.current_ts,
        initial_exchange_date=issuance_date,
        maturity_date=maturity_date,
        notional_principal=DEMO_NOTIONAL_PRINCIPAL,
        nominal_interest_rate=DEMO_FCB_NOMINAL_RATE,
        interest_payment_cycle=DEMO_FIXED_COUPON_PAYMENT_CYCLE,
        interest_payment_anchor=first_coupon_date,
    )
    normalized = normalize_contract_attributes(
        attrs,
        denomination_asset_id=context.denomination_asset.asset_id,
        denomination_asset_decimals=context.denomination_asset.decimals,
        notional_unit_value=DEMO_NOTIONAL_UNIT_VALUE,
        secondary_market_opening_date=issuance_date,
        secondary_market_closure_date=maturity_date + cst.DAY_2_SEC,
    )
    return DemoInstrumentSpec(
        label="FCB",
        prospectus_url=DEMO_FCB_PROSPECTUS_URL,
        normalized=normalized,
    )


def build_zero_coupon_bond_demo(context: DemoDeploymentContext) -> DemoInstrumentSpec:
    issuance_date = context.current_ts + _cycle_duration_seconds(
        DEMO_ISSUANCE_DELAY_CYCLE
    )
    maturity_date = issuance_date + _cycle_duration_seconds(DEMO_ZCB_MATURITY_CYCLE)
    discount_amount = DEMO_NOTIONAL_PRINCIPAL * DEMO_ZCB_DISCOUNT_BPS // cst.BPS

    attrs = make_pam_zero_coupon_bond(
        contract_id=2,
        status_date=context.current_ts,
        initial_exchange_date=issuance_date,
        maturity_date=maturity_date,
        notional_principal=DEMO_NOTIONAL_PRINCIPAL,
        premium_discount_at_ied=discount_amount,
    )
    normalized = normalize_contract_attributes(
        attrs,
        denomination_asset_id=context.denomination_asset.asset_id,
        denomination_asset_decimals=context.denomination_asset.decimals,
        notional_unit_value=DEMO_NOTIONAL_UNIT_VALUE,
        secondary_market_opening_date=issuance_date,
        secondary_market_closure_date=maturity_date + cst.DAY_2_SEC,
    )
    return DemoInstrumentSpec(
        label="ZCB",
        prospectus_url=DEMO_ZCB_PROSPECTUS_URL,
        normalized=normalized,
    )


def _client_terms(result: NormalizationResult) -> NormalizedActusTerms:
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


def _client_initial_state(result: NormalizationResult) -> InitialKernelState:
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


def _client_schedule_page(
    page: tuple[ExecutionScheduleEntry, ...],
) -> list[tuple[int, int, int, int, int, int, int, int, int]]:
    from d_asa.registry import EVENT_TYPE_IDS

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


def _fund_app_account(
    *,
    algorand: algokit_utils.AlgorandClient,
    payer: SigningAccount,
    app_address: str,
) -> None:
    funding_amount = int(
        os.getenv("APP_ACCOUNT_FUNDING_ALGO", str(DEMO_APP_FUNDING_ALGO))
    )
    algorand.send.payment(
        PaymentParams(
            sender=payer.address,
            signer=payer.signer,
            receiver=app_address,
            amount=AlgoAmount.from_algo(funding_amount),
        )
    )


def _configure_demo_app(
    *,
    client: DasaClient,
    spec: DemoInstrumentSpec,
) -> None:
    client.send.contract_config(
        ContractConfigArgs(
            terms=_client_terms(spec.normalized),
            initial_state=_client_initial_state(spec.normalized),
            prospectus=Prospectus(hash=bytes(32), url=spec.prospectus_url),
        ),
        params=CommonAppCallParams(max_fee=AlgoAmount.from_micro_algo(5_000)),
        send_params=SendParams(cover_app_call_inner_transaction_fees=True),
    )

    pages = spec.normalized.schedule_pages(cst.SCHEDULE_PAGE_SIZE)
    for index, page in enumerate(pages):
        client.send.contract_schedule(
            ContractScheduleArgs(
                schedule_page_index=index,
                is_last_page=index == len(pages) - 1,
                schedule_page=_client_schedule_page(page),
            ),
            params=CommonAppCallParams(max_fee=AlgoAmount.from_micro_algo(5_000)),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )


def _needs_configuration(
    *,
    client: DasaClient,
    operation: algokit_utils.OperationPerformed,
) -> bool:
    if operation in (
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ):
        return True
    return client.state.global_state.status == enums.STATUS_INACTIVE


def _deploy_instrument(
    *,
    app_name: str,
    factory: DasaFactory,
    arranger: SigningAccount,
    deployer: SigningAccount,
    algorand: algokit_utils.AlgorandClient,
    build_spec: Callable[[DemoDeploymentContext], DemoInstrumentSpec],
    demo_context: DemoDeploymentContext | None,
) -> DemoDeploymentContext | None:
    client, result = factory.deploy(
        app_name=app_name,
        create_params=DasaMethodCallCreateParams(
            args=ContractCreateArgs(arranger=arranger.address)
        ),
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    if not _needs_configuration(client=client, operation=result.operation_performed):
        logger.info(
            "%s app %s already configured at app id %s; skipped configuration",
            app_name,
            result.operation_performed.name,
            client.app_id,
        )
        return demo_context

    if demo_context is None:
        demo_context = _get_demo_context(algorand=algorand, deployer=deployer)
    spec = build_spec(demo_context)

    _fund_app_account(
        algorand=algorand,
        payer=deployer,
        app_address=client.app_address,
    )
    _configure_demo_app(client=client, spec=spec)
    logger.info(
        "Configured %s demo app at app id %s (%s)",
        spec.label,
        client.app_id,
        result.operation_performed.name,
    )
    return demo_context


# define deployment behaviour based on supplied app spec
def deploy() -> None:
    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")
    arranger = _get_arranger_account(algorand=algorand, deployer=deployer)

    factory = algorand.client.get_typed_app_factory(
        DasaFactory,
        default_sender=arranger.address,
        default_signer=arranger.signer,
    )

    demo_context: DemoDeploymentContext | None = None
    for app_name, build_spec in (
        (DEMO_FCB_APP_NAME, build_fixed_coupon_bond_demo),
        (DEMO_ZCB_APP_NAME, build_zero_coupon_bond_demo),
    ):
        demo_context = _deploy_instrument(
            app_name=app_name,
            factory=factory,
            arranger=arranger,
            deployer=deployer,
            algorand=algorand,
            build_spec=build_spec,
            demo_context=demo_context,
        )
