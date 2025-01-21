# Early Repayment Options {#early-repayment-options}

> Debt instruments could have early repayment options to repay the principal to
> investors (partially or totally) before maturity.

> Debt instrument with defined maturity date may terminate earlier if the full principal
> redemption happens earlier than maturity.

If the debt instrument has early repayment options, the D-ASA **MUST** implement
the **OPTIONAL** `set_early_repayment_time_events` \\([PP]\\) and `early_repayment`
methods.

The early repayment options **MAY** repay the *principal* partially or totally.

The early repayment options **MAY** repay the *principal* to all or some Lenders.

In the case of an on-chain payment agent, the D-ASA **MUST** repay the *principal*
to the Investor Payment Addresses.

In case of early repayment options, the D-ASA units associated with the early repaid
principal **MUST** be removed from Lenders’ Accounts and circulation.

## Penalties

The D-ASA **MAY** define a *penalty type* \\([PYTP]\\) for the early repayment option.

The *penalty type* **MUST** be identified with one of the following enumerated IDs
(`uint8`):

| ID    |            Name            | ACTUS Acronym | Description                                                                                            |
|:------|:--------------------------:|---------------|:-------------------------------------------------------------------------------------------------------|
| `0`   |         No Penalty         | \\([N]\\)     | No penalty applies                                                                                     |
| `1`   |       Fixed Penalty        | \\([A]\\)     | A fixed amount applies as penalty                                                                      |
| `2`   |      Relative Penalty      | \\([R]\\)     | A penalty relative to the notional outstanding applies                                                 |
| `3`   | Interest Rate Differential | \\([I]\\)     | A penalty based on the current interest rate differential relative to the notional outstanding applies |
| `255` |       Custom Penalty       | -             | Custom penalty                                                                                         |

The D-ASA **MAY** define a *penalty rate* \\([PYRT]\\) (`uint64`) for the amount
of the penalty.

> The *penalty rate* is either the absolute amount or the rate of the penalty.

The *penalty type* and the *penalty rate* **MAY** be set using the **OPTIONAL**
`set_asset_metadata` method (see [Metadata](./metadata.md) section).

> The implementation **SHOULD** manage the accrued interest on early repayments.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a *principal* of 1M EUR and a *minimum
> denomination* of 1,000 EUR. The D-ASA originally had 1,000 *total units* in circulation.
> An early repayment of 500k EUR (equal to 500 units) is executed for some Lenders.
> The D-ASA now has 500 circulating units (worth 1,000 EUR each), while 500 early
> repaid units are removed from circulation.

## Early Repayment Schedule

If the D-ASA has early repayment options, it **MUST** define *early repayment
time events* as `uint64[]` array, where:

- The length of the array **MUST** be `N>=2`;

- The first element **MUST** be the *early repayment start date* (`uint64`): the
time after which early repayment options could be executed;

- The last element **MUST** be the *early repayment end date* (`uint64`): the time
after which early repayment options cannot be executed.

The *early repayment time events* **MUST** be sorted in strictly ascending order.

The *early repayment start date* **MUST NOT** be earlier than the *issuance date*.

The *early repayment end date* **MUST NOT** be later than the *maturity date*.

In case of non-continuous *day-count conventions* (`ID<255`, see [Day-Count Conventions](./day-count-convention.md)
section), the *time periods* between subsequent events **MUST** be multiples of a
day, in seconds (`86400`).

The *early repayment time events* **MUST** be set with the `set_early_repayment_time_events`
method.

The *early repayment time events* **MAY** be updated with the `set_early_repayment_time_events`
method.

The updated *early repayment time events* **MUST NOT** modify past events.
