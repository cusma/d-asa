# Day-Count Convention {#day-count-convention}

> Debt instruments use a [day-count convention](https://en.wikipedia.org/wiki/Day_count_convention)
> to calculate the amount of accrued interest when the next coupon payment is less
> than a full coupon period away.

The D-ASA **MUST** specify one *day-count convention* \\( [IPCD] \\).

The *day-count convention* **MUST** be identified with one of the following enumerated
IDs (`uint8`):

| ID    |     Name      | ACTUS              | Description                                                                                                              |
|:------|:-------------:|--------------------|:-------------------------------------------------------------------------------------------------------------------------|
| `0`   | Actual/Actual | \\([AA]\\)         | Year fractions accrue on the basis of the actual number of days per month and per year in the respective period          |
| `1`   |  Actual/360   | \\([A360]\\)       | Year fractions accrue on the basis of the actual number of days per month and 360 days per year in the respective period |
| `2`   |  Actual/365   | \\([A365]\\)       | Year fractions accrue on the basis of the actual number of days per month and 365 days per year in the respective period |
| `3`   |  30/360 ISDA  | \\([30E360ISDA]\\) | Year fractions accrue on the basis of 30 days per month and 360 days per year in the respective period (ISDA method)     |
| `4`   |    30/360     | \\([30E360]\\)     | Year fractions accrue on the basis of 30 days per month and 360 days per year in the respective period                   |
| `5`   |    28/366     | \\([28E366]\\)     | Year fractions accrue on the basis of 28 days per month and 366 days per year in the respective period                   |
| `6`   |    30/365     | -                  | Year fractions accrue on the basis of 30 days per month and 365 days per year in the respective period                   |

## Calendar

> Calendars define the non-working days which may affect the dates of traditional
> debt instruments.

> The AVM (so the D-ASA) time has no notion of calendars. Conversion of serial UNIX
> timestamps into a year/month/day triple[^1] (and vice versa) can be performed
> by external Algorand Applications[^2] or client side (normalization).

The D-ASA **MAY** specify a *calendar* \\( [CLDR] \\).

The *calendar* **MUST** be identified with one of the following enumerated IDs:

| ID    |       Name       | ACTUS      | Description                                    |
|:------|:----------------:|------------|:-----------------------------------------------|
| `0`   |   No Calendar    | \\([NC]\\) | No holidays defined (default if not specified) |
| `1`   | Monday to Friday | \\([MF]\\) | Saturdays and Sundays are holidays             |

## Business Day Convention

> Debt instruments cash flows execution may be stopped on non-working days (according
> to a calendar).

> The business day convention defines how D-ASA execution can be shifted to the
> next business day (following) or the previous on (preceding).

The D-ASA **MAY** specify a *business day convention* \\( [BDC] \\).

## End of Month Convention

> Debt instruments may define due dates as the last day of the month.

> The end-of-month convention defines how D-ASA execution can be shifted according
> to the different number of days in months (31, 30, and 28) according to the calendar.

The D-ASA **MAY** specify a *end-of-month convention* \\( [EOMC] \\).

## Normalization profile restrictions

The D-ASA kernel **MUST** store one normalized day-count convention identifier.

The current kernel accepts the following identifiers:

| ID  | Name          | ACTUS        |
|:----|:--------------|:-------------|
| `0` | Actual/Actual | `AA`         |
| `1` | Actual/360    | `A360`       |
| `2` | Actual/365    | `A365`       |
| `3` | 30E/360 ISDA  | `30E360ISDA` |
| `4` | 30E/360       | `30E360`     |

A contract configuration **MUST** fail if the normalized terms use any other day-count
identifier.

The current D-ASA ACTUS profile imposes the following additional constraints on
date handling:

- `business_day_convention` **MUST** be `NOS`;
- `calendar` **MUST** be `NC`;
- Timestamps **MUST** be expressed as UTC UNIX seconds.

Those constraints are enforced during normalization so that the AVM only receives
values that can be executed deterministically without external calendar logic.

## Accrual factors

The AVM kernel does not recompute year fractions from raw dates. Instead, normalization
**MUST** precompute the relevant accrual factors and place them in each `ExecutionScheduleEntry`.

This split is intentional:

- Date arithmetic and ACTUS schedule generation happen off chain;
- Execution, validation, and state transitions happen on chain.

---

[^1]: The paper *"chrono-Compatible Low-Level Date Algorithms"* (<a href="https://howardhinnant.github.io/date_algorithms.html">ref</a>),
by Howard Hinnant, provides a list of algorithms for the conversion of serial UNIX
time into a <a href="https://en.wikipedia.org/wiki/Proleptic_Gregorian_calendar">proleptic
Gregorian calendar</a> (and vice versa).

[^2]: An <a href="https://github.com/code-alexander/py2algo/blob/main/py2algo/projects/py2algo/smart_contracts/time/contract.py">example</a>
of Algorand Application implementing the conversion of serial UNIX time into a proleptic
Gregorian calendar year/month/day triple.
