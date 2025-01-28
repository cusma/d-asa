# Performance {#performance}

> Debt instruments performances are exposed to credit risks.

The D-ASA *performance* \\([PRF]\\) **MUST** be identified with one of the following
enumerated IDs (`uint8`):

| ID  |    Name    | ACTUS Acronym | Description                                                                          |
|:----|:----------:|---------------|:-------------------------------------------------------------------------------------|
| `0` | Performant | \\([PF]\\)    | Contract is performing according to terms and conditions                             |
| `1` |  Delayed   | \\([DL]\\)    | Contractual payment obligations are delayed according to the *grace period*          |
| `2` | Delinquent | \\([DQ]\\)    | Contractual payment obligations are delinquent according to the *delinquency period* |
| `3` |  Default   | \\([DF]\\)    | Contract defaulted on payment obligations according to *delinquency period*          |
| `4` |  Matured   | \\([MA]\\)    | Contract matured                                                                     |
| `5` | Terminated | \\([TE]\\)    | Contract has been terminated                                                         |

## Grace Period {#grace-period}

> Debt instruments may define a grace period as a time window after the payment
> due date during which payment may be retried without a penalty.

The D-ASA **MAY** define a *grace period* \\([GRP]\\) (`uint64`).

The *grace period* **MUST** be defined as UNIX time, in seconds.

In case of non-continuous *day-count conventions* (`ID<255`, see [Day-Count Conventions](./day-count-convention.md)
section), the *grace period* **MUST** be multiples of a day, in seconds (`86400`).

The *grace period* **MAY** be set using the `asset_config` method as *time period*
with:

- The *time period duration* (`uint64`) equal to the *grace period* duration;

- The *time period repetitions* (`uint64`) equal to `1`.

- The *grace period* **MUST** be anchored \\([ANX]\\) to the *time event* of the
first failed payment.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with a *grace period*. A D-ASA coupon payment is triggered
> on due date, but there is not enough liquidity to pay all the investors. The D-ASA
> program starts counting the *grace period*, increments a failed payments counter,
> and waits 3 hours to retry. If the D-ASA payment retrial succeeds within the *grace
> period*, no penalty or fee is applied.

## Delinquency Period {#delinquency-period}

> Debt instruments may define a delinquency period as a time window after the grace
> period. If payment happens after the delinquency period, then the counterparty
> is in technical default.

The D-ASA **MAY** define a *delinquency period* \\([DQP]\\) (`uint64`).

The *delinquency period* **MUST** be defined as UNIX time, in seconds.

In case of non-continuous *day-count conventions* (`ID<255`, see [Day-Count Conventions](./day-count-convention.md)
section), the *delinquency period* **MUST** be multiples of a day, in seconds (`86400`).

The *delinquency period* **MAY** be set using the `asset_config` method as *time
period* with:

- The *time period duration* (`uint64`) equal to the *delinquency period* duration;

- The *time period repetitions* (`uint64`) equal to `1`.

- The *delinquency period* **MUST** be anchored \\([ANX]\\) to the *time event*
of the first failed payment or at the end of the *grace period* (if any).

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with a *delinquency period*. A D-ASA coupon payment is triggered
> on due date, but there is not enough liquidity to pay all the investors. The D-ASA
> program starts counting the *delinquency period*, increments a failed payments
> counter, and waits 3 hours to retry. If the D-ASA payment retrial succeeds within
> the *delinquency period*, a penalty or fee is applied.

## Default

> Default is the ultimate failure to pay the lenders according to the payment obligations.
> When this happens, the creditors have the right to declare default to the debtors.

> Default processes require the intervention of regulatory bodies and courts, therefore
> the D-ASA default status bridges the default process off-chain.

The D-ASA **SHOULD** enter *default* status if it cannot perform payments on due
dates.

The D-ASA **MAY** disable all non-administrative methods on *default* status.

> The D-ASA default can be called either automatically (based on program conditions)
> or manually (based on the decision of a trustee).

The *default* status **MAY** be set with the **OPTIONAL** `set_default_status` method.

> 📎 **EXAMPLE**
>
> The D-ASA has no *grace period* and no *delinquency period*. A D-ASA coupon payment
> is triggered on due date, but there is not enough liquidity to pay all the investors.
> The D-ASA contract automatically enters in *default* immediately.

> 📎 **EXAMPLE**
>
> The D-ASA has a *grace period* and a *delinquency period*. A D-ASA coupon payment
> is triggered on due date, but there is not enough liquidity to pay all the investors.
> The D-ASA program starts counting the *grace period* and *delinquency period*.
> If the *delinquency period* expires, then the contract enters in *default*.

> 📎 **EXAMPLE**
>
> A D-ASA coupon payment is triggered on due date, but there is not enough liquidity
> to pay all the investors. The D-ASA contract relies on a trustee to call the *default*.
