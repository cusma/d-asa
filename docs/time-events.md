# Time Events {#time-events}

The D-ASA **MUST** define *time events* as `uint64[]` array, where:

- The length of the array **MUST** be:

  - `N=K+4`, if the D-ASA **has** a *maturity date;*
  - `N=K+3`, if the D-ASA **has not** a *maturity date;*

  with `K` equal to the *total coupons*.

- The first element **MUST** be the *primary distribution opening date* (`uint64`):
the time at which the D-ASA primary distribution opens;

- The second element **MUST** be the *primary distribution closure date* (`uint64`):
the time at which the D-ASA primary distribution closes;

- The third element **MUST** be the *issuance date* (`uint64`): the time at which
D-ASA starts to accrue interest on the principal;

- If the D-ASA has a **defined** number of *coupons*, the next `K`-elements **MUST**
be the *coupon due dates* (`uint64[K]`): times at which the D-ASA can pay coupons;

- If the D-ASA **has** a *maturity date*, the last element **MUST** be the *maturity
date* (`uint64`).

The *time events* **MUST** be sorted in strictly ascending order.

The *time events* **SHOULD** be defined as UNIX time, in seconds.

In the case of *time events* defined in UNIX time and non-continuous *day-count
conventions* (ID<`255`, see [Day-Count Conventions](./day-count-convention.md) section),
the *time periods* between subsequent events **MUST** be multiples of a day, in
seconds (`86400`).

The *time events* **MUST** be set using the `asset_config` method.

> 📎 **EXAMPLE**
>
> The following are valid *time events* (UNIX times):
>
> ```text
> uint64[] = [1704067200, 1735603200, 1767139200, 1798675200, 1830211200]
> ```

> 📎 **EXAMPLE**
>
> The following are invalid (respectively unsorted and not-strictly sorted) *time
> events* (UNIX times):
>
> ```text
> uint64[] = [1830211200, 1704067200, 1735603200, 1767139200, 1798675200]
> ```
>
> ```text
> uint64[] = [1704067200, 1735603200, 1767139200, 1798675200, 1830211200, 1830211200]
> ```

> 📎 **EXAMPLE**
>
> A D-ASA with `K` *total coupons* and a **defined** *maturity date*, has the following
> *time events*:
>
> ```text
> uint64[] = [primary_distribution_opening_date, primary_distribution_closure_date, issuance_date, cupon_due_date_1, ..., coupon_due_date_K, maturity_date]
> ```

> 📎 **EXAMPLE**
>
> A D-ASA whose primary distribution lasts from December 1st, 2023 00:00:00 GMT+0
> to December 15th, 2023 00:00:00 GMT+0, is issued on January 1st, 2024 00:00:00
> GMT+0 and matures on January 1st, 2028 00:00:00 GMT+0, with 4 annual coupons,
> each paid on December 31st 00:00:00 GMT+0, has the following *time events* array
> (UNIX times):
>
> ```text
> uint64[] = [1701388800, 1702598400, 1704067200, 1735603200, 1767139200, 1798675200, 1830211200, 1830297600]
> ```

> 📎 **EXAMPLE**
>
> A D-ASA whose primary distribution lasts from December 1st, 2023 00:00:00 GMT+0
> to December 15th, 2023 00:00:00 GMT+0, is issued on January 1st, 2024 00:00:00
> GMT+0 and matures on January 1st, 2028 00:00:00 GMT+0, with zero coupons, has
> the following *time events* array (UNIX times):
>
> ```text
> uint64[] = [1701388800, 1702598400, 1704067200, 1830297600]
> ```

> 📎 **EXAMPLE**
>
> A D-ASA whose primary distribution lasts from December 1st, 2023 00:00:00 GMT+0
> to December 15th, 2023 00:00:00 GMT+0, is issued on January 1st, 2024 00:00:00
> GMT+0 and no maturity, with perpetual coupons, has the following *time events*
> array (UNIX times):
>
> ```text
> uint64[] = [1701388800, 1702598400, 1704067200]
> ```
