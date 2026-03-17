# Payment Agent {#payment-agent}

> Debt instruments' cash flows usually involve:
> - *Principal repayment*
> - *Early principal repayments*
> - *Interest payments*

The Payment Agent executes ACTUS cashflows in two phases:

1. `fund_due_cashflows`
1. `claim_due_cashflows`

## Funding phase

`fund_due_cashflows` **MUST**:

- Inspect the schedule at the current global cursor;
- Process only due cash events (`IP`, `PR`, `MD`);
- Compute contract-wide interest and principal due from the normalized schedule;
- Reserve settlement funds in the contract;
- Convert those amounts into cumulative per-unit indices;
- Advance the global event cursor.

If an Op Daemon address is configured, `fund_due_cashflows` **MUST** only accept
calls from:

- The Op Daemon;
- The Arranger.

If no Op Daemon is configured, the current implementation applies no extra caller
restriction beyond the contract checks.

## Claim phase

`claim_due_cashflows` **MUST**:

- Settle the holder position to the latest cumulative indices;
- Expose the holder's claimable interest and principal amounts;
- Execute an on-chain transfer if the payment address is executable;
- Otherwise leave the claimable amounts reserved for a later attempt.

The method **MUST** return an opaque `payment_info` context unchanged so callers
can bind off-chain metadata to the claim.

> The payment information could be used, for example, for:
> - Adding unique identifiers or external context to the payments;
> - Enabling external payment system integration in the case of off-chain settlement;
> - Providing information about the settled amount and conversion rate used with
> respect to the denomination asset.

## Authorization model

If an Op Daemon address is configured, `claim_due_cashflows` **MUST** only accept
calls from:

- The Op Daemon;
- The Account *holding address*;
- The Account *payment address*.

If no Op Daemon is configured, the current implementation applies no extra caller
restriction beyond the contract and account checks.
