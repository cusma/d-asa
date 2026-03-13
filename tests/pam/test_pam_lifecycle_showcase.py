from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts import constants as cst
from smart_contracts import enums
from src import NormalizationResult, normalize_contract_attributes
from src.artifacts.dasa_client import (
    ClaimDueCashflowsArgs,
    DasaClient,
    FundDueCashflowsArgs,
)
from src.contracts import make_pam_fixed_coupon_bond_profile, make_pam_zero_coupon_bond
from src.registry import EVENT_TYPE_IDS
from src.schedule import Cycle
from tests import utils
from tests.pam.pam_test_support import (
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

NOMINAL_RATE = 0.02
INTEREST_PAYMENT_CYCLE = Cycle.parse_cycle("90D")
MATURITY_OFFSET_CYCLE = Cycle.parse_cycle("1800D")
ZERO_COUPON_MATURITY_CYCLE = Cycle.parse_cycle("360D")
ZERO_COUPON_DISCOUNT_BPS = 200


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
    currency: utils.Currency,
) -> PamShowcaseScenario:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    issuance_delay = cycle_duration_seconds(ISSUANCE_DELAY_CYCLE)
    coupon_period = cycle_duration_seconds(INTEREST_PAYMENT_CYCLE)
    maturity_offset = cycle_duration_seconds(MATURITY_OFFSET_CYCLE)
    assert maturity_offset % coupon_period == 0
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
    assert [entry.event_type for entry in normalized.schedule] == [
        "IED",
        *(["IP"] * total_coupons),
        "MD",
    ]
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
    currency: utils.Currency,
) -> PamShowcaseScenario:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
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
    assert [entry.event_type for entry in normalized.schedule] == ["IED", "MD"]

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


def _run_showcase_scenario(
    *,
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    d_asa_client: DasaClient,
    pam_primary_dealer: utils.DAsaPrimaryDealer,
    pam_account_manager: utils.DAsaAccountManager,
    scenario: PamShowcaseScenario,
) -> PamLifecycleTrace:
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
    assert initial_state.status == enums.STATUS_PENDING_IED
    assert initial_state.schedule_entry_count == len(scenario.normalized.schedule)

    ied_entry = scenario.normalized.schedule[0]
    utils.time_warp(ied_entry.scheduled_time + cst.DAY_2_SEC)
    ied_result = client.send.contract_execute_ied()
    ied_event = utils.decode_actus_execution_event(
        utils.get_event_from_call_result(ied_result)
    )
    assert ied_event["event_id"] == ied_entry.event_id
    assert ied_event["event_type"] == EVENT_TYPE_IDS["IED"]
    assert ied_event["scheduled_time"] == ied_entry.scheduled_time
    assert ied_event["payoff"] == scenario.investor_payment_amount
    assert ied_event["payoff_sign"] == enums.PAYOFF_SIGN_POSITIVE
    assert ied_event["settled_amount"] == 0
    assert ied_event["sequence"] == ied_entry.event_id + 1

    steps: list[PamLifecycleTraceStep] = [
        PamLifecycleTraceStep(
            schedule_entry=ied_entry,
            execution_event=ied_event,
            funded_amount=0,
            execution_tx_id=utils.get_primary_tx_id(ied_result),
        )
    ]

    active_state = client.send.contract_get_state().abi_return
    assert active_state.status == enums.STATUS_ACTIVE
    assert active_state.event_cursor == 1

    total_interest_claimed = 0
    total_principal_claimed = 0

    for entry in scenario.normalized.schedule[1:]:
        utils.time_warp(entry.scheduled_time)

        funding_result = client.send.fund_due_cashflows(
            FundDueCashflowsArgs(max_event_count=1)
        )
        funding = funding_result.abi_return
        assert funding.processed_events == 1
        assert funding.total_funded > 0

        event = utils.decode_actus_execution_event(
            utils.get_event_from_call_result(funding_result)
        )
        assert event["event_id"] == entry.event_id
        assert event["event_type"] == EVENT_TYPE_IDS[entry.event_type]
        assert event["scheduled_time"] == entry.scheduled_time
        assert event["payoff"] == funding.total_funded
        assert event["payoff_sign"] == enums.PAYOFF_SIGN_NEGATIVE
        assert event["settled_amount"] == funding.total_funded
        assert event["sequence"] == entry.event_id + 1

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

        assert claim.total_amount == funding.total_funded
        assert balance_after - balance_before == claim.total_amount

        steps.append(
            PamLifecycleTraceStep(
                schedule_entry=entry,
                execution_event=event,
                funded_amount=funding.total_funded,
                execution_tx_id=utils.get_primary_tx_id(funding_result),
                claim=make_claim_trace(
                    interest_amount=claim.interest_amount,
                    principal_amount=claim.principal_amount,
                    total_amount=claim.total_amount,
                    timestamp=claim.timestamp,
                ),
                claim_tx_id=utils.get_primary_tx_id(claim_result),
            )
        )
        total_interest_claimed += claim.interest_amount
        total_principal_claimed += claim.principal_amount

    final_state = client.send.contract_get_state().abi_return
    assert final_state.status == enums.STATUS_ENDED
    assert final_state.event_cursor == len(scenario.normalized.schedule)
    assert total_interest_claimed == scenario.expected_total_interest_amount
    assert total_principal_claimed == scenario.normalized.terms.notional_principal

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


SHOWCASE_BUILDERS: tuple[
    Callable[[AlgorandClient, utils.Currency], PamShowcaseScenario],
    ...,
] = (
    _build_fixed_coupon_showcase,
    _build_zero_coupon_showcase,
)


@pytest.mark.parametrize(
    "build_scenario",
    SHOWCASE_BUILDERS,
    ids=("fcb", "zcb"),
)
def test_pam_lifecycle_showcase(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    d_asa_client: DasaClient,
    pam_primary_dealer: utils.DAsaPrimaryDealer,
    pam_account_manager: utils.DAsaAccountManager,
    build_scenario: Callable[[AlgorandClient, utils.Currency], PamShowcaseScenario],
) -> None:
    """
    Run with `pytest -s` to print the normalized ACTUS schedule beside the
    real ARC-28 execution proofs and realized holder cashflows.
    """

    scenario = build_scenario(algorand, currency)
    trace = _run_showcase_scenario(
        algorand=algorand,
        bank=bank,
        currency=currency,
        d_asa_client=d_asa_client,
        pam_primary_dealer=pam_primary_dealer,
        pam_account_manager=pam_account_manager,
        scenario=scenario,
    )

    print()
    print(format_lifecycle_trace(trace))
