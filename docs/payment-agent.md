# Payment Agent {#payment-agent}

> Debt instruments' cash flows usually involve:
>
> - *Principal repayment*
> - *Early repayments*
> - *Coupon payments*

> D-ASA cash flows might not be executed synchronously for all the Investors. The
> execution of a given cash flow could last a few blocks[^1], depending on the number
> of payees.

> Although a single block proposer could order transactions in a block, in a healthy
> network block proposers are selected randomly by the Algorand consensus. Therefore,
> order of payments in a block is random and unbiased, with no systematic advantage
> or precedence of a payee with respect to others.

> D-ASA supports both on-chain and off-chain payment agents, depending on the settlement
> asset (see [Settlement](./settlement.md) section).

> For reference implementations using on-chain payment agents, the AVM fees (ALGO)
> for the cash flows execution **SHOULD** be paid by who triggers the cash flows.

> A reference implementation of an on-chain payment agent **SHOULD NOT** require
> extra fees for the cash flows execution.

The D-ASA payment methods **MAY** provide additional information about the payment.

> The payment information could be used, for example, for:
>
> - Adding unique identifiers or external context to the payments;
> - Enabling external payment system integration in the case of off-chain settlement;
> - Providing information about the settled amount and conversion rate used with
> respect to the denomination asset.

---

[^1]: The Algorand protocol has dynamic block latency with instant finality. At
the time of writing (Jan 2025), block finality is about 2.8 seconds, the block size
is 5 MB, resulting in theoretical throughput of 10,000 transactions per second.
