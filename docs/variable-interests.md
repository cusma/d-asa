# Variable Rates

> Debt instruments may have variable interest rates, based on external data oracles.

If the debt instrument has *variable interest rates*, the D-ASA **MAY** implement
the **OPTIONAL** `set_variable_interest` method.

## Spread

> Debt instruments typically define a spread (bps) with respect to an external index
> to update the interest rate.

The D-ASA **MAY** define a *rate spread* \\([RRSP]\\) (`uint16`) in *bps* to apply
to the external interest data feed.

The *rate spread* **MUST** be set using the **OPTIONAL** `set_variable_rate` method.

If the debt instrument has no *rate spread*, then the D-ASA **MUST** set the *rate
spread* to `0`.

> 📎 **EXAMPLE**
>
> A D-ASA has variable interest rates pegged to an off-chain index. Interest update
> is equal to the off-chain index plus the *rate spread* (bps).

## Cap and Floor

> Debt instruments may define limitations to the interest rate variability, either
> over the whole contract lifespan or over specific periods.

### Life

The D-ASA **MAY** define a *life cap* \\([RRLC]\\) (`uint16`) in *bps* to apply
to the variable *interest rate*.

The D-ASA **MAY** define a *life floor* \\([RRLF]\\) (`uint16`) in *bps* to apply
to the variable *interest rate*.

The *life cap* and the *life floor* **MUST** be set using the **OPTIONAL** `set_variable_rate`
method.

If the debt instrument has no *life cap*, then the D-ASA **MUST** set the *life
cap* to `0`.

If the debt instrument has no *life floor*, then the D-ASA **MUST** set the *life
floor* to `0`.

### Period

The D-ASA **MAY** define a *period cap* \\([RRPC]\\) (`uint16`) in *bps* to apply
to the variable *interest rate*.

The D-ASA **MAY** define a *period floor* \\([RRPF]\\) (`uint16`) in *bps* to
apply to the variable *interest rate*.

The *period cap* and the *period floor* **MUST** be set using the **OPTIONAL** `set_variable_rate`
method.

If the debt instrument has no *period cap*, then the D-ASA **MUST** set the *period
cap* to `0`.

If the debt instrument has no *period floor*, then the D-ASA **MUST** set the *period
floor* to `0`.

## Fixing Period

> Debt instruments usually schedule interest rate updates before the new rate applies
> (defined by the rate reset schedule).

The D-ASA **MUST** define a *fixing period* \\([RRFIX]\\) (`uint64`) that specifies
a period of time before the *coupon due date* in which the interest can be updated.

The *fixing period* **MUST** be set using the **OPTIONAL** `set_variable_rate` method.

## Rates Update

> Debt instruments may have a fixed or undefined rate update schedule.

If the debt instrument has a **fixed** rate update schedule, then the D-ASA **MUST**
use the *coupon due dates* (either *time events* or *time periods*) as anchors for
the rate update events (see [Time Schedule](./time-schedule.md) section).

The *interest rate* **MAY** be updated using the **OPTIONAL** `update_interest_rate`
method.

If the D-ASA has coupons, the *interest rate* **MUST NOT** be updated if there is
any due coupon still to be paid.

The *coupon rates* **MAY** be updated using the **OPTIONAL** `update_coupon_rates`
method.

The *coupon rates* **MUST NOT** be updated if there is any due coupon still to be
paid.

The updated *coupon rates* **MUST NOT** modify past coupon rates.

The *interest rate* and *coupon rates* updatability **MUST** be restricted to the
*interest oracle* role (see [Oracles](./roles.md#oracles) section).

> 📎 **EXAMPLE**
>
> A D-ASA has variable interest rates pegged to an off-chain index. Interest update
> permissions are granted to an external interest oracle.

> 📎 **EXAMPLE**
>
> A D-ASA has variable interest rates based on covenant breaches. Interest update
> permissions are granted to a trustee in charge of verifying breaches.
