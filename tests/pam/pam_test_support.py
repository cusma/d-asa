from __future__ import annotations

from dataclasses import dataclass

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
from smart_contracts.artifacts.d_asa.dasa_client import (
    AccountOpenArgs,
    ContractConfigArgs,
    ContractCreateArgs,
    ContractScheduleArgs,
    DasaClient,
    DasaFactory,
    InitialKernelState,
    NormalizedActusTerms,
    PrimaryDistributionArgs,
    Prospectus,
    RbacAssignRoleArgs,
)
from src import NormalizationResult
from src.registry import EVENT_TYPE_IDS
from src.schedule import Cycle
from tests import conftest_helpers as role_helpers
from tests import utils

PRINCIPAL = 10_000
MINIMUM_DENOMINATION = 100
ISSUANCE_DELAY_CYCLE = Cycle.parse_cycle("30D")


@dataclass(frozen=True)
class PamLifecycleContext:
    client: DasaClient
    investor: SigningAccount
    receiver: SigningAccount


def asset_balance(algorand: AlgorandClient, *, address: str, asset_id: int) -> int:
    return algorand.client.algod.account_asset_info(address, asset_id)["asset-holding"][
        "amount"
    ]


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
    page: tuple,
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
    algorand: AlgorandClient,
    arranger: SigningAccount,
    bank: SigningAccount,
    currency: utils.Currency,
    normalized: NormalizationResult,
    bank_funding_amount: int,
    investor_payment_amount: int,
    prospectus_url: str,
) -> PamLifecycleContext:
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
        min_spending_balance=AlgoAmount.from_algo(10_000),
    )

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

    primary_dealer = role_helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )
    account_manager = role_helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
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
        asset_balance(algorand, address=investor.address, asset_id=currency.id)
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

    assert asset_balance(algorand, address=investor.address, asset_id=currency.id) == 0
    assert (
        asset_balance(algorand, address=client.app_address, asset_id=currency.id)
        == bank_funding_amount + investor_payment_amount
    )

    return PamLifecycleContext(
        client=client,
        investor=investor,
        receiver=receiver,
    )
