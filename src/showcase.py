from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AssetCreateParams,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts import constants as cst
from smart_contracts import enums
from src import NormalizationResult, normalize_contract_attributes
from src.artifacts.dasa_client import (
    ClaimDueCashflowsArgs,
    ContractCreateArgs,
    DasaClient,
    DasaFactory,
    FundDueCashflowsArgs,
    RbacAssignRoleArgs,
    RoleValidity,
)
from src.contracts import make_pam_fixed_coupon_bond_profile, make_pam_zero_coupon_bond
from src.localnet import (
    Currency,
    DAsaAccountManager,
    DAsaPrimaryDealer,
    LocalNetConfig,
    algorand_client_from_localnet,
    decode_actus_execution_event,
    get_event_from_call_result,
    get_latest_timestamp,
    get_primary_tx_id,
    load_localnet_config,
    time_warp,
)
from src.pam_lifecycle import (
    ISSUANCE_DELAY_CYCLE,
    MINIMUM_DENOMINATION,
    PRINCIPAL,
    PamLifecycleTrace,
    PamLifecycleTraceStep,
    cycle_duration_seconds,
    format_lifecycle_trace,
    make_claim_trace,
    setup_pam_lifecycle,
)
from src.registry import EVENT_TYPE_IDS
from src.schedule import Cycle

INITIAL_ALGO_FUNDS = AlgoAmount.from_algo(10_000)
DENOMINATION_ASA_NAME = "Euro"
DENOMINATION_ASA_UNIT = "EUR"
DENOMINATION_ASA_DECIMALS = 2
DENOMINATION_ASA_SCALE = 10**DENOMINATION_ASA_DECIMALS
DENOMINATION_ASA_TOTAL = 10_000_000 * DENOMINATION_ASA_SCALE

NOMINAL_RATE = 0.02
INTEREST_PAYMENT_CYCLE = Cycle.parse_cycle("90D")
MATURITY_OFFSET_CYCLE = Cycle.parse_cycle("1800D")
ZERO_COUPON_MATURITY_CYCLE = Cycle.parse_cycle("360D")
ZERO_COUPON_DISCOUNT_BPS = 200

RoleAccountType = TypeVar("RoleAccountType", bound=SigningAccount)


@dataclass(frozen=True, slots=True)
class PamShowcaseScenario:
    title: str
    contract_variant: str
    description: str
    normalized: NormalizationResult
    bank_funding_amount: int
    investor_payment_amount: int
    expected_total_interest_amount: int


def _derive_total_interest_amount(result: NormalizationResult) -> int:
    outstanding_principal = result.schedule[0].next_outstanding_principal
    nominal_interest_rate = (
        result.schedule[0].next_nominal_interest_rate or result.terms.rate_reset_next
    )
    accrued_interest = 0
    total_interest = 0

    for entry in result.schedule[1:]:
        interest_segment = (
            outstanding_principal
            * nominal_interest_rate
            // result.terms.fixed_point_scale
            * entry.accrual_factor
            // result.terms.fixed_point_scale
        )

        if entry.event_type in {"IP", "MD"}:
            total_interest += accrued_interest + interest_segment
            accrued_interest = 0
        elif entry.event_type == "PR":
            accrued_interest += interest_segment

        if entry.event_type in {"PR", "MD"}:
            outstanding_principal = entry.next_outstanding_principal

        if entry.next_nominal_interest_rate:
            nominal_interest_rate = entry.next_nominal_interest_rate

    return total_interest


def _build_fixed_coupon_showcase(
    algorand: AlgorandClient,
    currency: Currency,
) -> PamShowcaseScenario:
    current_ts = get_latest_timestamp(algorand.client.algod)
    issuance_delay = cycle_duration_seconds(ISSUANCE_DELAY_CYCLE)
    coupon_period = cycle_duration_seconds(INTEREST_PAYMENT_CYCLE)
    maturity_offset = cycle_duration_seconds(MATURITY_OFFSET_CYCLE)
    if maturity_offset % coupon_period != 0:
        raise ValueError("Maturity offset must be an exact multiple of coupon period")
    total_coupons = maturity_offset // coupon_period

    issuance_date = current_ts + issuance_delay
    first_coupon_date = issuance_date + coupon_period
    maturity_date = issuance_date + maturity_offset

    attrs = make_pam_fixed_coupon_bond_profile(
        contract_id=1,
        status_date=current_ts,
        initial_exchange_date=issuance_date,
        maturity_date=maturity_date,
        notional_principal=PRINCIPAL,
        nominal_interest_rate=NOMINAL_RATE,
        interest_payment_cycle=INTEREST_PAYMENT_CYCLE,
        interest_payment_anchor=first_coupon_date,
    )
    normalized = normalize_contract_attributes(
        attrs,
        denomination_asset_id=currency.id,
        denomination_asset_decimals=currency.decimals,
        notional_unit_value=MINIMUM_DENOMINATION,
        secondary_market_opening_date=issuance_date,
        secondary_market_closure_date=maturity_date + cst.DAY_2_SEC,
    )
    if [entry.event_type for entry in normalized.schedule] != [
        "IED",
        *(["IP"] * total_coupons),
        "MD",
    ]:
        raise ValueError("Unexpected normalized schedule for fixed coupon showcase")
    total_interest_amount = _derive_total_interest_amount(normalized)

    return PamShowcaseScenario(
        title="D-ASA lifecycle showcase: PAM fixed coupon bond",
        contract_variant="PAM:FCB",
        description=f"{total_coupons} coupon periods at {NOMINAL_RATE:.2%} nominal rate",
        normalized=normalized,
        bank_funding_amount=total_interest_amount,
        investor_payment_amount=normalized.terms.initial_exchange_amount,
        expected_total_interest_amount=total_interest_amount,
    )


def _build_zero_coupon_showcase(
    algorand: AlgorandClient,
    currency: Currency,
) -> PamShowcaseScenario:
    current_ts = get_latest_timestamp(algorand.client.algod)
    issuance_delay = cycle_duration_seconds(ISSUANCE_DELAY_CYCLE)
    maturity_offset = cycle_duration_seconds(ZERO_COUPON_MATURITY_CYCLE)

    issuance_date = current_ts + issuance_delay
    maturity_date = issuance_date + maturity_offset
    discount_amount = PRINCIPAL * ZERO_COUPON_DISCOUNT_BPS // cst.BPS

    attrs = make_pam_zero_coupon_bond(
        contract_id=2,
        status_date=current_ts,
        initial_exchange_date=issuance_date,
        maturity_date=maturity_date,
        notional_principal=PRINCIPAL,
        premium_discount_at_ied=discount_amount,
    )
    normalized = normalize_contract_attributes(
        attrs,
        denomination_asset_id=currency.id,
        denomination_asset_decimals=currency.decimals,
        notional_unit_value=MINIMUM_DENOMINATION,
        secondary_market_opening_date=issuance_date,
        secondary_market_closure_date=maturity_date + cst.DAY_2_SEC,
    )
    if [entry.event_type for entry in normalized.schedule] != ["IED", "MD"]:
        raise ValueError("Unexpected normalized schedule for zero coupon showcase")

    return PamShowcaseScenario(
        title="D-ASA lifecycle showcase: PAM zero coupon bond",
        contract_variant="PAM:ZCB",
        description=f"{ZERO_COUPON_DISCOUNT_BPS / cst.BPS:.2%} discount at issuance, single maturity redemption",
        normalized=normalized,
        bank_funding_amount=normalized.terms.notional_principal
        - normalized.terms.initial_exchange_amount,
        investor_payment_amount=normalized.terms.initial_exchange_amount,
        expected_total_interest_amount=0,
    )


SHOWCASE_BUILDERS: tuple[
    Callable[[AlgorandClient, Currency], PamShowcaseScenario],
    ...,
] = (
    _build_fixed_coupon_showcase,
    _build_zero_coupon_showcase,
)


def run_showcase_scenario(
    *,
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: Currency,
    d_asa_client: DasaClient,
    pam_primary_dealer: DAsaPrimaryDealer,
    pam_account_manager: DAsaAccountManager,
    build_scenario: Callable[[AlgorandClient, Currency], PamShowcaseScenario],
) -> PamLifecycleTrace:
    scenario = build_scenario(algorand, currency)
    participants = setup_pam_lifecycle(
        client=d_asa_client,
        primary_dealer=pam_primary_dealer,
        account_manager=pam_account_manager,
        algorand=algorand,
        bank=bank,
        currency=currency,
        normalized=scenario.normalized,
        bank_funding_amount=scenario.bank_funding_amount,
        investor_payment_amount=scenario.investor_payment_amount,
        prospectus_url=scenario.title,
    )
    investor = participants.investor
    client = d_asa_client

    initial_state = client.send.contract_get_state().abi_return
    if initial_state.status != enums.STATUS_PENDING_IED:
        raise ValueError("Contract must start in PENDING_IED")
    if initial_state.schedule_entry_count != len(scenario.normalized.schedule):
        raise ValueError("Unexpected schedule length in showcase contract state")

    ied_entry = scenario.normalized.schedule[0]
    time_warp(ied_entry.scheduled_time + cst.DAY_2_SEC, algorand=algorand)
    ied_result = client.send.contract_execute_ied()
    ied_event = decode_actus_execution_event(get_event_from_call_result(ied_result))
    if ied_event["event_id"] != ied_entry.event_id:
        raise ValueError("Unexpected IED event id")
    if ied_event["event_type"] != EVENT_TYPE_IDS["IED"]:
        raise ValueError("Unexpected IED event type")
    if ied_event["scheduled_time"] != ied_entry.scheduled_time:
        raise ValueError("Unexpected IED scheduled time")
    if ied_event["payoff"] != scenario.investor_payment_amount:
        raise ValueError("Unexpected IED payoff")
    if ied_event["payoff_sign"] != enums.PAYOFF_SIGN_POSITIVE:
        raise ValueError("Unexpected IED payoff sign")
    if ied_event["settled_amount"] != 0:
        raise ValueError("IED should not settle holder cashflows")
    if ied_event["sequence"] != ied_entry.event_id + 1:
        raise ValueError("Unexpected IED sequence")

    steps: list[PamLifecycleTraceStep] = [
        PamLifecycleTraceStep(
            schedule_entry=ied_entry,
            execution_event=ied_event,
            funded_amount=0,
            execution_tx_id=get_primary_tx_id(ied_result),
        )
    ]

    active_state = client.send.contract_get_state().abi_return
    if active_state.status != enums.STATUS_ACTIVE:
        raise ValueError("Contract must become ACTIVE after IED")
    if active_state.event_cursor != 1:
        raise ValueError("Unexpected event cursor after IED")
    total_interest_claimed = 0
    total_principal_claimed = 0

    for entry in scenario.normalized.schedule[1:]:
        time_warp(entry.scheduled_time, algorand=algorand)

        funding_result = client.send.fund_due_cashflows(
            FundDueCashflowsArgs(max_event_count=1)
        )
        funding = funding_result.abi_return
        event = decode_actus_execution_event(get_event_from_call_result(funding_result))
        if funding.processed_events != 1:
            raise ValueError("Showcase funding should process exactly one event")
        if funding.total_funded <= 0:
            raise ValueError("Showcase funding must reserve a positive amount")
        if event["event_id"] != entry.event_id:
            raise ValueError("Unexpected funding event id")
        if event["event_type"] != EVENT_TYPE_IDS[entry.event_type]:
            raise ValueError("Unexpected funding event type")
        if event["scheduled_time"] != entry.scheduled_time:
            raise ValueError("Unexpected funding scheduled time")
        if event["payoff"] != funding.total_funded:
            raise ValueError("Unexpected funding payoff")
        if event["payoff_sign"] != enums.PAYOFF_SIGN_NEGATIVE:
            raise ValueError("Unexpected funding payoff sign")
        if event["settled_amount"] != funding.total_funded:
            raise ValueError("Unexpected settled amount")
        if event["sequence"] != entry.event_id + 1:
            raise ValueError("Unexpected funding sequence")

        balance_before = algorand.asset.get_account_information(
            investor.address,
            currency.id,
        ).balance
        claim_result = client.send.claim_due_cashflows(
            ClaimDueCashflowsArgs(
                holding_address=investor.address,
                payment_info=b"",
            ),
            params=CommonAppCallParams(
                sender=investor.address,
                signer=investor.signer,
                max_fee=AlgoAmount.from_micro_algo(3_000),
            ),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )
        claim = claim_result.abi_return
        balance_after = algorand.asset.get_account_information(
            investor.address,
            currency.id,
        ).balance

        if claim.total_amount != funding.total_funded:
            raise ValueError("Claimed amount does not match funded amount")
        if balance_after - balance_before != claim.total_amount:
            raise ValueError("Investor settlement balance does not match claim amount")

        steps.append(
            PamLifecycleTraceStep(
                schedule_entry=entry,
                execution_event=event,
                funded_amount=funding.total_funded,
                execution_tx_id=get_primary_tx_id(funding_result),
                claim=make_claim_trace(
                    interest_amount=claim.interest_amount,
                    principal_amount=claim.principal_amount,
                    total_amount=claim.total_amount,
                    timestamp=claim.timestamp,
                ),
                claim_tx_id=get_primary_tx_id(claim_result),
            )
        )
        total_interest_claimed += claim.interest_amount
        total_principal_claimed += claim.principal_amount

    final_state = client.send.contract_get_state().abi_return
    if final_state.status != enums.STATUS_ENDED:
        raise ValueError("Showcase contract did not end cleanly")
    if final_state.event_cursor != len(scenario.normalized.schedule):
        raise ValueError("Unexpected final event cursor")
    if total_interest_claimed != scenario.expected_total_interest_amount:
        raise ValueError("Unexpected total claimed interest")
    if total_principal_claimed != scenario.normalized.terms.notional_principal:
        raise ValueError("Unexpected total claimed principal")

    return PamLifecycleTrace(
        title=scenario.title,
        contract_variant=scenario.contract_variant,
        description=scenario.description,
        normalized=scenario.normalized,
        currency_decimals=currency.decimals,
        currency_unit_name=currency.unit_name,
        investor_payment_amount=scenario.investor_payment_amount,
        total_interest_claimed=total_interest_claimed,
        total_principal_claimed=total_principal_claimed,
        status_before_ied=initial_state.status,
        status_after_ied=active_state.status,
        final_status=final_state.status,
        steps=tuple(steps),
    )


def _create_funded_account(algorand: AlgorandClient) -> SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return account


def _create_currency(algorand: AlgorandClient, bank: SigningAccount) -> Currency:
    currency_id = algorand.send.asset_create(
        AssetCreateParams(
            sender=bank.address,
            signer=bank.signer,
            total=DENOMINATION_ASA_TOTAL,
            decimals=DENOMINATION_ASA_DECIMALS,
            asset_name=DENOMINATION_ASA_NAME,
            unit_name=DENOMINATION_ASA_UNIT,
        )
    ).asset_id

    return Currency(
        id=currency_id,
        total=DENOMINATION_ASA_TOTAL,
        decimals=DENOMINATION_ASA_DECIMALS,
        name=DENOMINATION_ASA_NAME,
        unit_name=DENOMINATION_ASA_UNIT,
        asa_to_unit=1 / 10**DENOMINATION_ASA_DECIMALS,
    )


def _create_dasa_client(
    algorand: AlgorandClient,
    arranger: SigningAccount,
) -> DasaClient:
    factory = algorand.client.get_typed_app_factory(
        DasaFactory,
        default_sender=arranger.address,
        default_signer=arranger.signer,
    )
    client, _ = factory.send.create.contract_create(
        ContractCreateArgs(arranger=arranger.address)
    )
    algorand.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return client


def _create_role_account(
    algorand: AlgorandClient,
    role_account_class: type[RoleAccountType],
    client: DasaClient,
) -> RoleAccountType:
    account = _create_funded_account(algorand)
    role_account = role_account_class(private_key=account.private_key)
    client.send.rbac_assign_role(
        RbacAssignRoleArgs(
            role_id=role_account.role_id(),
            role_address=role_account.address,
            validity=RoleValidity(
                role_validity_start=0,
                role_validity_end=2**64 - 1,
            ),
        )
    )
    return role_account


def run_showcase_suite(
    localnet_config: LocalNetConfig | None = None,
) -> tuple[PamLifecycleTrace, ...]:
    algorand = algorand_client_from_localnet(
        localnet_config or load_localnet_config(default_host="host.docker.internal")
    )
    arranger = _create_funded_account(algorand)
    bank = _create_funded_account(algorand)
    traces: list[PamLifecycleTrace] = []

    for build_scenario in SHOWCASE_BUILDERS:
        currency = _create_currency(algorand, bank)
        d_asa_client = _create_dasa_client(algorand, arranger)
        pam_primary_dealer = _create_role_account(
            algorand,
            DAsaPrimaryDealer,
            d_asa_client,
        )
        pam_account_manager = _create_role_account(
            algorand,
            DAsaAccountManager,
            d_asa_client,
        )
        traces.append(
            run_showcase_scenario(
                algorand=algorand,
                bank=bank,
                currency=currency,
                d_asa_client=d_asa_client,
                pam_primary_dealer=pam_primary_dealer,
                pam_account_manager=pam_account_manager,
                build_scenario=build_scenario,
            )
        )

    return tuple(traces)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the D-ASA LocalNet showcase scenarios.",
    )
    parser.add_argument("--localnet-host", help="Override the LocalNet host.")
    parser.add_argument("--localnet-token", help="Override the LocalNet API token.")
    parser.add_argument("--algod-port", type=int, help="Override the algod port.")
    parser.add_argument("--kmd-port", type=int, help="Override the kmd port.")
    parser.add_argument("--indexer-port", type=int, help="Override the indexer port.")
    return parser


def _config_from_args(args: argparse.Namespace) -> LocalNetConfig:
    base = load_localnet_config(default_host="host.docker.internal")
    return LocalNetConfig(
        host=args.localnet_host or base.host,
        token=args.localnet_token or base.token,
        algod_port=args.algod_port or base.algod_port,
        kmd_port=args.kmd_port or base.kmd_port,
        indexer_port=args.indexer_port or base.indexer_port,
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    traces = run_showcase_suite(_config_from_args(args))
    for index, trace in enumerate(traces):
        if index:
            print()
        print(format_lifecycle_trace(trace))


if __name__ == "__main__":
    main()
