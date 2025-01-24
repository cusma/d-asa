# Time Events {#time-events}

> D-ASA *time events* are time on which contractual events are due or on which cyclic
> events begin or end.

## Primary Distribution {#primary-distribution}

> Debt instruments can be distributed on the primary market during the primary distribution.

> The opening and closure dates define the primary distribution duration.

The D-ASA **MUST** have a *primary opening* (`uint64`) and *closure date* (`uint64`).

## Issuance {#issuance}

> Debt instruments start accruing interest on the issuance date.

The D-ASA **MUST** have an *issuance date* \\([IED]\\) (`uint64`).

## Maturity {#maturity}

> Debt instruments may have a maturity date, on which the principal is repaid and
> the contract obligations expire.

> Debt instruments may have a fixed or variable maturity date.

The D-ASA **MAY** have a *maturity date* \\([MD]\\) (`uint64`).

The *maturity date* **MAY** be updated in case of early repayment options (see
[Early Repayment Options](./early-repayment-options.md) section).

## Time Events array

The D-ASA **MUST** define *time events* \\([TEV]\\) as `uint64[]` array, where:

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

- If the D-ASA has a **fixed** number of *coupons*, then the next `K`-elements
**MUST** be the *coupon due dates* \\([IP]\\) (`uint64[K]`): times at which the
coupons mature and the interest payment \\([IPPNT]\\) can be executed[^1]. The first
coupon due date corresponds to \\([IPANX]\\).

- If the D-ASA has **unlimited** number of *coupons*, then `K` **MUST** be `0` and
*coupons due dates* \\([IP]\\) are managed with *time periods* (see [Time Periods](./time-periods.md#unlimited-time-schedule)
section).

- If the D-ASA **has** a *maturity date*, the last element **MUST** be the *maturity
date* (`uint64`).

The *time events* **MUST** be sorted in strictly ascending order.

The *time events* **MUST** be defined as UNIX time, in seconds.

In the case of non-continuous *day-count conventions* (`ID<255`, see [Day-Count
Conventions](./day-count-convention.md) section), the *time periods* between subsequent
events **MUST** be multiples of a day, in seconds (`86400`)[^2].

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

---

[^1]: The D-ASA supports just interest payments at the end of each coupon period.

[^2]: This applies to any kind of time event (e.g., principal and interest payments,
primary and secondary market dates, early repayments options, interest updates,
etc.)
