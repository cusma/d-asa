# Time Schedule {#time-schedule}

> Debt instruments may have fixed or variable time events (e.g. variable coupon
> due date, etc.).

> Debt instruments may have a defined or undefined number of time events (e.g. a
> fixed coupon bond or a perpetual bond).

> Time on the AVM can be expressed as the block's height (round) or block’s timestamp
> (UNIX time). The block’s time is dynamic, so D-ASA based on the block’s height
> could present a drift with external time references.

## Primary Distribution {#primary-distribution}

> Debt instruments can be distributed on the primary market during the primary distribution.

> The opening and closure dates define the primary distribution duration.

The D-ASA **MUST** have a *primary opening* and *closure date*.

## Issuance {#issuance}

> Debt instruments start accruing interest on the issuance date.

The D-ASA **MUST** have an *issuance date*.

## Maturity {#maturity}

> Debt instruments may have a maturity date, on which the principal is repaid and
> the contract obligations expire.

> Debt instruments may have a fixed or variable maturity date.

The D-ASA **MAY** have a *maturity date*.
