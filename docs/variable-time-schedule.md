# Variable Time Schedule {#variable-time-schedule}

> Debt instruments can have variable time schedule, based on different contract
> terms, such as covenants, etc.

## Variable Time Events {#variable-time-events}

The *time events* **MAY** be updated with the **OPTIONAL** `update_time_events`
method.

The updated *time events* **MUST NOT** modify past events.

> A reference implementation **SHOULD** restrict the time events updatability.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with a *maturity date* and 4 coupons, defined by *time events*.
> The 2nd coupon is due.
>
> The updated time events **can no longer** modify:
>
> - the *primary distribution opening date*;
> - the *primary distribution closure date*;
> - the *issuance date*;
> - the 1st and 2nd coupon due dates.
>
> The updated time events **can still** modify:
>
> - the 3rd and 4th coupon due dates;
> - the *maturity date*.

## Variable Time Periods {#variable-time-periods}

The *time periods* **MAY** be updated with the **OPTIONAL** `update_time_periods`
method.

The updated *time periods* **MUST** preserve chronological consistency with respect
to the *time events*.

> A reference implementation **SHOULD** restrict the time periods updatability.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with an *issuance date* and a *maturity date*, defined as *time
> events*, and 4 coupons whose periods are defined by *time periods*.
>
> The sum of the 4 updated coupon *time period durations* must be smaller than the
> time period between the *issuance date* and the *maturity date*.
