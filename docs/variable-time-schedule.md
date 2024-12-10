# Variable Time Schedule {#variable-time-schedule}

The *time events* **MAY** be updated with the **OPTIONAL** `update_time_events`
method.

The updated *time events* **MUST NOT** modify past events.

> A reference implementation **SHOULD** restrict the time events updatability.

> 📎 **EXAMPLE**
>
> The 2nd coupon is due, so the updated time events can not modify the primary distribution
> opening and closure dates, the issuance date, and the 1st and 2nd coupon due dates.

The *time periods* **MAY** be updated with the **OPTIONAL** `update_time_periods`
method.

The updated *time periods* **MUST** preserve D-ASA chronological consistency.

> A reference implementation **SHOULD** restrict the time periods updatability.
