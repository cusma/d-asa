# Time Periods {#time-periods}

> D-ASA time periods can be used to define recurring time events.

The D-ASA **MAY** define *time periods* as `(uint64,uint64)[]` array, where:

- The first element of the tuple defines the *time period duration* (`uint64`).
It **MUST** be strictly greater than `0`;

- The second element of the tuple defines the *time period repetitions* (`uint64`).
It **MUST** be `0` if *repetitions* are **unlimited**.

The *time periods* **SHOULD** be defined as UNIX time, in seconds.

In the case of *time periods* defined in UNIX time and non-continuous *day-count
conventions* (ID<`255`, see Day-Count Conventions section), the *time periods*
**SHOULD** be multiples of a day, in seconds (`86400`).

The *time periods* **MAY** be set using the `asset_config` method.

If the D-ASA does not implement *time periods,* it **MUST** be set to `[]` in the
`asset_config` method.

> 📎 **EXAMPLE**
>
> The following are valid time periods (UNIX times) indicating a daily time even
> with unlimited repetitions and a monthly (30 days) time event with 12 repetitions:
>
> ```text
> (uint64,uint64)[] = [(86400, 0), (2592000, 12)]
> ```

> 📎 **EXAMPLE**
>
> The following are invalid time periods (UNIX times):
>
> ```text
> (uint64,uint64)[] = [(0, 0), (0, 12)]
> ```
