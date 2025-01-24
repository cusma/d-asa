# Early Repayment Options {#early-repayment-options}

> Debt instruments could have early repayment options to repay the principal to
> investors (partially or totally) before maturity or to reduce the maturity date.

> Debt instrument with defined maturity date may terminate earlier if the full principal
> redemption happens earlier than maturity.

If the debt instrument has early repayment options, the D-ASA **MUST** implement
the **OPTIONAL** `set_early_repayment_option` method.

## Early Repayment Schedule

If the D-ASA has early repayment options, it **MUST** define *early repayment time
events* as `uint64[]` array, where:

- The length of the array **MUST** be `N>=1`;

- The first element **MUST** be the *early repayment start date* \\([OPANX]\\) (`uint64`):
the time after which early repayment options could be executed;

- If the D-ASA has a *maturity date*, the last element **MUST** be the *early repayment
end date* \\([OPXED]\\) (`uint64`): the time after which early repayment options
cannot be executed.

The *early repayment time events* **MUST** be sorted in strictly ascending order.

The *early repayment start date* **MUST NOT** be earlier than the *issuance date*.

The *early repayment end date* **MUST NOT** be later than the *maturity date*.

The unscheduled *prepayment events* \\([PP]\\) **MUST** occur within the defined
*early repayment schedule*.

In the case of non-continuous *day-count conventions* (`ID<255`, see [Day-Count
Conventions](./day-count-convention.md) section), the *time periods* between subsequent
events **MUST** be multiples of a day, in seconds (`86400`).

The *early repayment time events* **MUST** be set with the `set_early_repayment_time_events`
method.

The *early repayment time events* **MAY** be updated with the `set_early_repayment_time_events`
method.

The updated *early repayment time events* **MUST NOT** modify past events.

## Prepayment Effects

An early repayment option could have different *prepayment effects* \\([PPEF]\\):

- It **MAY** repay the *principal* partially or totally, to all or some Investors
before the *maturity date* (see [Early Repayment](./early-repayment.md) section);

- It **MAY** reduce the *maturity date* (see [Variable Time Schedule](./variable-time-schedule.md)
section).

The *prepayment effect* **MUST** be identified with one of the following enumerated
IDs (`uint8`):

| ID    |                 Name                 | ACTUS Acronym | Description                                                                                     |
|:------|:------------------------------------:|---------------|:------------------------------------------------------------------------------------------------|
| `0`   |            No Prepayment             | \\([N]\\)     | Prepayment is not allowed under the agreement                                                   |
| `1`   | Prepayment Reduces Redemption Amount | \\([A]\\)     | Prepayment is allowed and reduces the redemption amount for the remaining period up to maturity |
| `2`   |     Prepayment Reduces Maturity      | \\([M]\\)     | Prepayment is allowed and reduces the maturity                                                  |
| `255` |                Custom                | -             | Prepayment is allowed and the effect is custom                                                  |

The *prepayment effect* **MAY** be set using the **OPTIONAL** `set_asset_metadata`
method (see [Metadata](./metadata.md) section).

> The implementation **SHOULD** manage the accrued interest on early repayments.

## Penalties

> Debt instruments may have a penalty as a consequence of an early repayment option.

The D-ASA **MAY** define a *penalty type* \\([PYTP]\\) (`uint8`) for the early repayment
options.

The *penalty type* **MUST** be identified with one of the following enumerated IDs:

| ID    |            Name            | ACTUS Acronym | Description                                                                                            |
|:------|:--------------------------:|---------------|:-------------------------------------------------------------------------------------------------------|
| `0`   |         No Penalty         | \\([N]\\)     | No penalty applies                                                                                     |
| `1`   |       Fixed Penalty        | \\([A]\\)     | A fixed amount applies as penalty                                                                      |
| `2`   |      Relative Penalty      | \\([R]\\)     | A penalty relative to the notional outstanding applies                                                 |
| `3`   | Interest Rate Differential | \\([I]\\)     | A penalty based on the current interest rate differential relative to the notional outstanding applies |
| `255` |           Custom           | -             | Custom penalty                                                                                         |

The *penalty type* **MAY** be set using the **OPTIONAL** `set_asset_metadata` method
(see [Metadata](./metadata.md) section).

If the debt instrument has a *penalty type* with `ID>0`, the D-ASA **MUST** define
a *penalty rate* \\([PYRT]\\) (`uint64`) for the amount of the penalty.

> The *penalty rate* is either the absolute amount or the rate of the penalty.

The *penalty rate* **MAY** be set using the **OPTIONAL** `set_early_repayment_option`
method (see [Metadata](./metadata.md) section).
