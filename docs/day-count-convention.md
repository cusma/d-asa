# Day-Count Convention {#day-count-convention}

> Debt instruments use a <a href="https://en.wikipedia.org/wiki/Day_count_convention">day-count
> convention</a> to calculate the amount of accrued interest when the next coupon
> payment is less than a full coupon period away.

The D-ASA **MUST** specify one *day-count convention* \\([IPCD]\\) (`uint8`).

The *day-count convention* **MUST** be identified with one of the following enumerated
IDs (`uint8`):

| ID    |     Name      | ACTUS              | Description                                                                                                              |
|:------|:-------------:|--------------------|:-------------------------------------------------------------------------------------------------------------------------|
| `0`   | Actual/Actual | \\([AA]\\)         | Year fractions accrue on the basis of the actual number of days per month and per year in the respective period          |
| `1`   |  Actual/360   | \\([A360]\\)       | Year fractions accrue on the basis of the actual number of days per month and 360 days per year in the respective period |
| `2`   |  Actual/365   | \\([A365]\\)       | Year fractions accrue on the basis of the actual number of days per month and 365 days per year in the respective period |
| `3`   |  30/360 ISDA  | \\([30E360ISDA]\\) | Year fractions accrue on the basis of 30 days per month and 360 days per year in the respective period (ISDA method)     |
| `4`   |    30/360     | \\([30E360]\\)     | Year fractions accrue on the basis of 30 days per month and 360 days per year in the respective period                   |
| `5`   |    28/366     | \\([28E336]\\)     | Year fractions accrue on the basis of 28 days per month and 366 days per year in the respective period                   |
| `6`   |    30/365     | -                  | Year fractions accrue on the basis of 30 days per month and 365 days per year in the respective period                   |
| `255` |  Continuous   | -                  | Time fractions accrue on the basis of the number of UNIX time units (non-leap seconds) in the respective time period     |

The *day-count convention* defines the *day-count factor* as a fraction of:

- Numerator: elapsed time of the accrual period to date;
- Denominator: time of the full accrual period defined by the *time schedule*.

The *day-count convention* **MUST** be set using the `asset_config` method.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA with the following coupon dates:
>
> - `date1`: starting date for the current coupon’s interest accrual, defined by
> the *time schedule*;
> - `date2`: date through which the interest is being accrued (“to” date), equals
> to the current block timestamp;
> - `date3`: next coupon due date, defined by the *time schedule*.
>
> The day-count factor is calculated as:
>
> **Continuous** (`255`) convention:
>
> ```text
> (date2 - date1) / (date3 - date1)
> ```
>
> **Actual/Actual** (`0`) convention:
>
> ```text
> days_in(date2 - date1) / days_in(date3 - date1)
> ```
>
> Where `days_in` returns the actual number of days (equal to `86400` seconds) in
> the time interval.

## Calendar

> Calendars define the non-working days which may affect the dates of traditional
> debt instruments.

> The AVM (so the D-ASA) time has no notion of calendars. Conversion of serial UNIX
> timestamps into a year/month/day triple[^1] (and vice versa) can be performed by
> external Algorand Applications[^2] or client side.

The D-ASA **MAY** specify a *calendar* \\([CLDR]\\).

The *calendar* **MUST** be identified with one of the following enumerated IDs (`uint8`):

| ID    |       Name       | ACTUS      | Description                                    |
|:------|:----------------:|------------|:-----------------------------------------------|
| `0`   |   No Calendar    | \\([NC]\\) | No holidays defined (default if not specified) |
| `1`   | Monday to Friday | \\([MF]\\) | Saturdays and Sundays are holidays             |
| `255` |      Custom      | -          | Custom holidays definition                     |

The *calendar* **MAY** be set using the **OPTIONAL** `set_asset_metadata` method
(see [Metadata](./metadata.md) section).

> A reference implementation **SHOULD** use the default *calendar* (`0`).

## Business Day Convention

> Debt instruments cash flows execution may be stopped on non-working days (according
> to a calendar).

> The business day convention defines how D-ASA execution can be shifted to the
> next business day (following) or the previous on (preceding).

The D-ASA **MAY** specify a *business day convention* \\([BDC]\\).

It is **RECOMMENDED** to use an ACTUS *business day convention*.

The *business day convention* **MAY** be set using the **OPTIONAL** `set_asset_metadata`
method (see [Metadata](./metadata.md) section).

> A reference implementation **SHOULD NOT** adopt a *business day convention* (as
> it has no defined calendar).

## End of Month Convention

> Debt instruments may define due dates as the last day of the month.

> The end-of-month convention defines how D-ASA execution can be shifted according
> to the different number of days in months (31, 30, and 28) according to the calendar.

The D-ASA **MAY** specify a *end-of-month convention* \\([EOMC]\\).

It is **RECOMMENDED** to use an ACTUS *end-of-month convention*.

The *end-of-month convention* **MAY** be set using the **OPTIONAL** `set_asset_metadata`
method (see [Metadata](./metadata.md) section).

> A reference implementation **SHOULD NOT** adopt an *end-of-month day convention*
> (as it has no defined calendar).

---

[^1]: The paper *"chrono-Compatible Low-Level Date Algorithms"* (<a href="https://howardhinnant.github.io/date_algorithms.html">ref</a>),
by Howard Hinnant, provides a list of algorithms for the conversion of serial UNIX
time into a <a href="https://en.wikipedia.org/wiki/Proleptic_Gregorian_calendar">proleptic
Gregorian calendar</a> (and vice versa).

[^2]: An <a href="https://github.com/code-alexander/py2algo/blob/main/py2algo/projects/py2algo/smart_contracts/time/contract.py">example</a>
of Algorand Application implementing the conversion of serial UNIX time into a proleptic
Gregorian calendar year/month/day triple.
