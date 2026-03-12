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
from src import normalize_contract_attributes
from src.contracts import make_pam_zero_coupon_bond
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

ZERO_COUPON_MATURITY_CYCLE = Cycle.parse_cycle("360D")
ZERO_COUPON_DISCOUNT_BPS = 200


def test_zero_coupon_pam_discounted_full_lifecycle(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    d_asa_client: DasaClient,
    pam_primary_dealer: utils.DAsaPrimaryDealer,
    pam_account_manager: utils.DAsaAccountManager,
) -> None:
    current_ts = utils.get_latest_timestamp(algorand.client.algod)
    issuance_delay = cycle_duration_seconds(ISSUANCE_DELAY_CYCLE)
    maturity_offset = cycle_duration_seconds(ZERO_COUPON_MATURITY_CYCLE)

    issuance_date = current_ts + issuance_delay
    maturity_date = issuance_date + maturity_offset
    discount_amount = PRINCIPAL * ZERO_COUPON_DISCOUNT_BPS // cst.BPS
    issue_price = PRINCIPAL - discount_amount
    currency_scale = 10**currency.decimals
    scaled_principal = scale_currency_amount(PRINCIPAL, currency_scale)
    scaled_issue_price = scale_currency_amount(issue_price, currency_scale)

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
    assert normalized.terms.initial_exchange_amount == scaled_issue_price
    assert normalized.terms.rate_reset_next == 0
    bank_funding_amount = scaled_principal - scaled_issue_price

    participants = setup_pam_lifecycle(
        client=d_asa_client,
        primary_dealer=pam_primary_dealer,
        account_manager=pam_account_manager,
        algorand=algorand,
        bank=bank,
        currency=currency,
        normalized=normalized,
        bank_funding_amount=bank_funding_amount,
        investor_payment_amount=normalized.terms.initial_exchange_amount,
        prospectus_url="ACTUS zero coupon PAM lifecycle",
    )
    client = d_asa_client
    investor = participants.investor
    receiver = participants.receiver

    account_position = client.send.account_get_position(
        AccountGetPositionArgs(holding_address=investor.address)
    ).abi_return
    assert account_position.units == 0
    assert account_position.reserved_units == normalized.terms.total_units

    contract_state = client.send.get_contract_state().abi_return
    assert contract_state.contract_type == CONTRACT_TYPE_IDS["PAM"]
    assert contract_state.status == enums.STATUS_PENDING_IED
    assert contract_state.total_units == normalized.terms.total_units
    assert contract_state.initial_exchange_amount == scaled_issue_price
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
    ied_result = client.send.execute_ied()
    ied_event = utils.decode_actus_execution_event(
        utils.get_event_from_call_result(ied_result)
    )
    assert ied_event["event_id"] == ied_entry.event_id
    assert ied_event["event_type"] == EVENT_TYPE_IDS["IED"]
    assert ied_event["scheduled_time"] == ied_entry.scheduled_time
    assert ied_event["applied_at"] > ied_event["scheduled_time"]
    assert ied_event["payoff"] == scaled_issue_price
    assert ied_event["payoff_sign"] == enums.PAYOFF_SIGN_POSITIVE
    assert ied_event["settled_amount"] == 0

    contract_state = client.send.get_contract_state().abi_return
    assert contract_state.status == enums.STATUS_ACTIVE
    assert contract_state.event_cursor == 1
    assert contract_state.initial_exchange_amount == scaled_issue_price
    assert contract_state.outstanding_principal == scaled_principal
    assert contract_state.interest_calculation_base == scaled_principal
    assert contract_state.nominal_interest_rate == 0
    assert contract_state.reserved_units_total == normalized.terms.total_units

    md_entry = normalized.schedule[1]
    utils.time_warp(md_entry.scheduled_time)

    funding_result = client.send.fund_due_cashflows(
        FundDueCashflowsArgs(max_event_count=1)
    )
    funding = funding_result.abi_return
    assert funding.processed_events == 1
    assert funding.total_funded == scaled_principal

    event = utils.decode_actus_execution_event(
        utils.get_event_from_call_result(funding_result)
    )
    assert event["event_id"] == md_entry.event_id
    assert event["event_type"] == EVENT_TYPE_IDS["MD"]
    assert event["scheduled_time"] == md_entry.scheduled_time
    assert event["applied_at"] >= event["scheduled_time"]
    assert event["payoff"] == scaled_principal
    assert event["payoff_sign"] == enums.PAYOFF_SIGN_NEGATIVE
    assert event["settled_amount"] == scaled_principal
    assert event["sequence"] == 2

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

    assert claim.total_amount == scaled_principal
    assert claim.interest_amount == 0
    assert claim.principal_amount == scaled_principal
    assert balance_after - balance_before == scaled_principal

    contract_state = client.send.get_contract_state().abi_return
    final_position = client.send.account_get_position(
        AccountGetPositionArgs(holding_address=investor.address)
    ).abi_return

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
