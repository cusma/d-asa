from __future__ import annotations

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts import constants as cst
from smart_contracts import enums
from smart_contracts.artifacts.d_asa.dasa_client import (
    AccountGetPositionArgs,
    ClaimDueCashflowsArgs,
    DasaClient,
    FundDueCashflowsArgs,
)
from src import NormalizationResult, normalize_contract_attributes
from src.contracts import make_pam_fixed_coupon_bond_profile
from src.registry import CONTRACT_TYPE_IDS, EVENT_TYPE_IDS
from src.schedule import Cycle
from tests import utils
from tests.pam.pam_test_support import (
    ISSUANCE_DELAY_CYCLE,
    MINIMUM_DENOMINATION,
    PRINCIPAL,
    assert_pending_ied_guards,
    cycle_duration_seconds,
    scale_currency_amount,
    setup_pam_lifecycle,
)

NOMINAL_RATE = 0.02
INTEREST_PAYMENT_CYCLE = Cycle.parse_cycle("90D")
MATURITY_OFFSET_CYCLE = Cycle.parse_cycle("1800D")


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


def test_fixed_coupon_pam_full_lifecycle(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    d_asa_client: DasaClient,
    pam_primary_dealer: utils.DAsaPrimaryDealer,
    pam_account_manager: utils.DAsaAccountManager,
) -> None:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    issuance_delay = cycle_duration_seconds(ISSUANCE_DELAY_CYCLE)
    coupon_period = cycle_duration_seconds(INTEREST_PAYMENT_CYCLE)
    maturity_offset = cycle_duration_seconds(MATURITY_OFFSET_CYCLE)
    assert maturity_offset % coupon_period == 0
    total_coupons = maturity_offset // coupon_period

    issuance_date = current_ts + issuance_delay
    first_coupon_date = issuance_date + coupon_period
    maturity_date = issuance_date + maturity_offset
    currency_scale = 10**currency.decimals
    scaled_principal = scale_currency_amount(PRINCIPAL, currency_scale)

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

    expected_event_types = ["IED"] + ["IP"] * total_coupons + ["MD"]
    assert [entry.event_type for entry in normalized.schedule] == expected_event_types
    total_interest_amount = _derive_total_interest_amount(normalized)

    participants = setup_pam_lifecycle(
        client=d_asa_client,
        primary_dealer=pam_primary_dealer,
        account_manager=pam_account_manager,
        algorand=algorand,
        bank=bank,
        currency=currency,
        normalized=normalized,
        bank_funding_amount=total_interest_amount,
        investor_payment_amount=normalized.terms.initial_exchange_amount,
        prospectus_url="ACTUS fixed coupon PAM lifecycle",
    )
    client = d_asa_client
    investor = participants.investor
    receiver = participants.receiver

    account_position = client.send.account_get_position(
        AccountGetPositionArgs(holding_address=investor.address)
    ).abi_return
    assert account_position.units == 0
    assert account_position.reserved_units == normalized.terms.total_units

    contract_state = client.send.contract_get_state().abi_return
    assert contract_state.contract_type == CONTRACT_TYPE_IDS["PAM"]
    assert contract_state.status == enums.STATUS_PENDING_IED
    assert contract_state.total_units == normalized.terms.total_units
    assert contract_state.initial_exchange_amount == scaled_principal
    assert contract_state.reserved_units_total == normalized.terms.total_units
    assert contract_state.event_cursor == 0
    assert contract_state.schedule_entry_count == len(normalized.schedule)

    assert_pending_ied_guards(
        client=client,
        investor=investor,
        receiver=receiver,
    )

    ied_entry = normalized.schedule[0]
    utils.time_warp(ied_entry.scheduled_time + cst.DAY_2_SEC)
    ied_result = client.send.contract_execute_ied()
    ied_event = utils.decode_actus_execution_event(
        utils.get_event_from_call_result(ied_result)
    )
    assert ied_event["event_id"] == ied_entry.event_id
    assert ied_event["event_type"] == EVENT_TYPE_IDS["IED"]
    assert ied_event["scheduled_time"] == ied_entry.scheduled_time
    assert ied_event["applied_at"] > ied_event["scheduled_time"]
    assert ied_event["payoff"] == normalized.terms.initial_exchange_amount
    assert ied_event["payoff_sign"] == enums.PAYOFF_SIGN_POSITIVE
    assert ied_event["settled_amount"] == 0

    contract_state = client.send.contract_get_state().abi_return
    assert contract_state.status == enums.STATUS_ACTIVE
    assert contract_state.event_cursor == 1
    assert contract_state.initial_exchange_amount == scaled_principal
    assert contract_state.outstanding_principal == scaled_principal
    assert contract_state.interest_calculation_base == scaled_principal
    assert contract_state.nominal_interest_rate == normalized.terms.rate_reset_next
    assert contract_state.reserved_units_total == normalized.terms.total_units

    total_interest_claimed = 0
    total_principal_claimed = 0

    first_coupon_expected_interest = (
        scaled_principal
        * normalized.terms.rate_reset_next
        // cst.FIXED_POINT_SCALE
        * normalized.schedule[1].accrual_factor
        // cst.FIXED_POINT_SCALE
    )

    for schedule_index, entry in enumerate(normalized.schedule[1:], start=1):
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
        assert event["applied_at"] >= event["scheduled_time"]
        assert event["payoff"] == funding.total_funded
        assert event["payoff_sign"] == enums.PAYOFF_SIGN_NEGATIVE
        assert event["settled_amount"] == funding.total_funded
        assert event["sequence"] == schedule_index + 1

        balance_before = algorand.asset.get_account_information(
            investor.address, currency.id
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
            investor.address, currency.id
        ).balance

        assert claim.total_amount == funding.total_funded
        assert balance_after - balance_before == claim.total_amount

        if schedule_index == 1:
            assert claim.interest_amount == first_coupon_expected_interest

        if entry.event_type == "IP":
            assert claim.interest_amount == claim.total_amount
            assert claim.principal_amount == 0
        else:
            assert entry.event_type == "MD"
            assert claim.principal_amount == scaled_principal
            assert claim.total_amount == scaled_principal

        total_interest_claimed += claim.interest_amount
        total_principal_claimed += claim.principal_amount

    contract_state = client.send.contract_get_state().abi_return
    final_position = client.send.account_get_position(
        AccountGetPositionArgs(holding_address=investor.address)
    ).abi_return

    assert total_principal_claimed == scaled_principal
    assert total_interest_claimed > 0
    assert contract_state.status == enums.STATUS_ENDED
    assert contract_state.event_cursor == len(normalized.schedule)
    assert contract_state.schedule_entry_count == len(normalized.schedule)
    assert contract_state.total_units == normalized.terms.total_units
    assert contract_state.reserved_units_total == 0
    assert contract_state.outstanding_principal == 0
    assert contract_state.reserved_interest == 0
    assert contract_state.reserved_principal == 0
    assert final_position.units == normalized.terms.total_units
    assert final_position.reserved_units == 0
    assert final_position.claimable_interest == 0
    assert final_position.claimable_principal == 0
    assert final_position.settled_cursor == len(normalized.schedule)
