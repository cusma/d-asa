import pytest
from algokit_utils import (
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from d_asa.artifacts.dasa_client import (
    ClaimDueCashflowsArgs,
    DasaClient,
    FundDueCashflowsArgs,
    TransferArgs,
)
from d_asa.pam_lifecycle import (
    EVENT_TYPE_NAMES,
    ISSUANCE_DELAY_CYCLE,
    LOCALNET_EXPLORER_TX_BASE_URL,
    MINIMUM_DENOMINATION,
    PRINCIPAL,
    STATUS_NAMES,
    PamLifecycleClaimTrace,
    PamLifecycleParticipants,
    PamLifecycleTrace,
    PamLifecycleTraceStep,
    client_initial_state,
    client_schedule_page,
    client_terms,
    cycle_duration_seconds,
    format_lifecycle_trace,
    make_claim_trace,
    scale_currency_amount,
    setup_pam_lifecycle,
)
from smart_contracts import errors as err

__all__ = [
    "EVENT_TYPE_NAMES",
    "ISSUANCE_DELAY_CYCLE",
    "LOCALNET_EXPLORER_TX_BASE_URL",
    "MINIMUM_DENOMINATION",
    "PRINCIPAL",
    "STATUS_NAMES",
    "PamLifecycleClaimTrace",
    "PamLifecycleParticipants",
    "PamLifecycleTrace",
    "PamLifecycleTraceStep",
    "assert_pending_ied_guards",
    "client_initial_state",
    "client_schedule_page",
    "client_terms",
    "cycle_duration_seconds",
    "format_lifecycle_trace",
    "make_claim_trace",
    "scale_currency_amount",
    "setup_pam_lifecycle",
]


def assert_pending_ied_guards(
    *,
    client: DasaClient,
    investor: SigningAccount,
    receiver: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.PENDING_IED):
        client.send.fund_due_cashflows(FundDueCashflowsArgs(max_event_count=1))

    with pytest.raises(LogicError, match=err.PENDING_IED):
        client.send.claim_due_cashflows(
            ClaimDueCashflowsArgs(
                holding_address=investor.address,
                payment_info=b"",
            ),
            params=CommonAppCallParams(
                sender=investor.address,
                signer=investor.signer,
            ),
        )

    with pytest.raises(LogicError, match=err.PENDING_IED):
        client.send.transfer(
            TransferArgs(
                sender_holding_address=investor.address,
                receiver_holding_address=receiver.address,
                units=1,
            ),
            params=CommonAppCallParams(
                sender=investor.address,
                signer=investor.signer,
            ),
        )
