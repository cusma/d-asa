# Time Periods {#time-periods}

> D-ASA time periods can be used to define recurring (or "cyclic") events.

> D-ASA time periods start on (are "anchored" to) *time events*.

The D-ASA **MAY** define *time periods* \\([CL]\\) as `(uint64,uint64)[]` array,
where:

- The first element of the tuple defines the *time period duration* (`uint64`).
It **MUST** be strictly greater than `0`;

- The second element of the tuple defines the *time period repetitions* (`uint64`).
It **MUST** be `0` if *repetitions* are **unlimited**;

The *time periods* **MUST** be anchored \\([ANX]\\) to a *time event* (see [Time
Events](./time-events.md) section).

> 📎 **EXAMPLE**
>
> A *time periods* defines periodic interest payments anchored to (starting from)
> the *issuance date*.

The *time periods* **MUST** be defined as UNIX time, in seconds.

In case of non-continuous *day-count conventions* (`ID<255`, see [Day-Count Conventions](./day-count-convention.md)
section), the *time periods* **MUST** be multiples of a day, in seconds (`86400`).

The *time periods* **MAY** be set using the `asset_config` method.

If the D-ASA does not implement *time periods,* it **MUST** be set to `[]` in the
`asset_config` method.

> 📎 **EXAMPLE**
>
> The following are valid *time periods* (UNIX times) indicating:
>
> - a daily time event with unlimited repetitions
> - a monthly (30 days) time event with 12 repetitions
>
> ```text
> (uint64,uint64)[] = [(86400, 0), (2592000, 12)]
> ```

> 📎 **EXAMPLE**
>
> The following are invalid *time periods* (UNIX times):
>
> ```text
> (uint64,uint64)[] = [(0, 0), (0, 12)]
> ```

The *time periods* **MUST** be chronologically consistent with respect to the *time
events*.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with an *issuance date* and a *maturity date*, defined as *time
> events*, and 4 coupons whose periods are defined by *time periods*.
>
> The sum of the 4 coupon *time period durations* must be smaller than the time
> period between the *issuance date* and the *maturity date*.
