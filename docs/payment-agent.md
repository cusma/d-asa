# Payment Agent {#payment-agent}

> Debt instruments' cash flows usually involve:
>
> - *Principal repayment*
> - *Early repayments*
> - *Coupon payments*

> D-ASA cash flows might not be executed synchronously for all the Investors. The
> execution of a given cash flow could last a few blocks, depending on the number
> of payees.

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
