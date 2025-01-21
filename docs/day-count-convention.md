# Day-Count Convention {#day-count-convention}

> Debt instruments use a <a href="https://en.wikipedia.org/wiki/Day_count_convention">day-count
> convention</a> to calculate the amount of accrued interest when the next coupon
> payment is less than a full coupon period away.

The D-ASA **MUST** specify one *day-count convention* \\([IPCD]\\) (`uint8`).

The *day-count convention* **MUST** be identified with one of the following enumerated
IDs (`uint8`):

| ID    |     Name      | ACTUS Acronym      | Daily interest calculation description                                                                                   |
|:------|:-------------:|--------------------|:-------------------------------------------------------------------------------------------------------------------------|
| `0`   | Actual/Actual | \\([AA]\\)         | Year fractions accrue on the basis of the actual number of days per month and per year in the respective period          |
| `1`   |  Actual/360   | \\([A360]\\)       | Year fractions accrue on the basis of the actual number of days per month and 360 days per year in the respective period |
| `2`   |  Actual/365   | \\([A365]\\)       | Year fractions accrue on the basis of the actual number of days per month and 365 days per year in the respective period |
| `3`   |  30/360 ISDA  | \\([30E360ISDA]\\) | Year fractions accrue on the basis of 30 days per month and 360 days per year in the respective period (ISDA method)     |
| `4`   |    30/360     | \\([30E360]\\)     | Year fractions accrue on the basis of 30 days per month and 360 days per year in the respective period                   |
| `5`   |    28/366     | \\([28E336]\\)     | Year fractions accrue on the basis of 28 days per month and 366 days per year in the respective period                   |
| `6`   |    30/365     | -                  | Year fractions accrue on the basis of 30 days per month and 365 days per year in the respective period                   |
| `255` |  Continuous   | -                  | Accrue on the basis of the actual number of time units in the respective time period                                     |

The *day-count convention* defines the *day-count factor* as a fraction of:

- Numerator: elapsed time of the accrual period to date;
- Denominator: time of the full accrual period defined by the D-ASA time schedule.

The *day-count convention* **MUST** be set using the `asset_config` method.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA with time events defined as block’s timestamps (UNIX time).
> The D-ASA has the following coupon dates:
>
> - `date1`: starting date for the current coupon’s interest accrual, defined by
> the D-ASA time schedule;
> - `date2`: date through which the interest is being accrued (“to” date), equals
> to the current block timestamp;
> - `date3`: next coupon due date, defined by the D-ASA time schedule.
>
> The day-count factor is calculated as:
>
> **Continuous** convention (ID=`255`):
>
> ```text
> (date2 - date1) / (date3 - date1)
> ```
>
> **Actual/Actual** convention (ID=`100`):
>
> ```text
> days_in(date2 - date1) / days_in(date3 - date1)
> ```
>
> Where `days_in` returns the actual number of days (equal to `86400` seconds) in
> the time interval.
