# Interests

> Debt instruments interest is calculated on a fixed or variable rate on the outstanding
> principal.

> The interest rate is the nominal yield paid by the debt instrument on the principal,
> usually expressed as *Annual Percentage Yield* (APY).

The D-ASA *interest rates* **MUST** be defined in *<a href="https://en.wikipedia.org/wiki/Basis_point">basis
points</a>* (*bps*).

## Interest Rate

The D-ASA **MUST** define a *nominal interest rate* \\([IPNR]\\) (`uint16`).

## Coupons

> Debt instruments can pay interest in periodic installments, called coupons.

> Coupons mature in a coupon period, according to a defined coupon schedule.

The D-ASA **MUST** define the number of *total coupons* `K` (`uint64`):

- `K>0` if the D-ASA has a **defined** number of coupons;
- `K=0` if the D-ASA has **zero** or **undefined** (perpetual) coupons.

## Coupon Rates

> Debt instruments can pay coupons with fixed or variable interest rates.

The D-ASA **MAY** define the *coupon rates* \\([ARRATE]\\) as `uint16[]` array,
where:

- The length of the array **MUST** be `K`, equal to the *total coupons*;
- The `K`\-elements of the array are the *coupon rates*, expressed in *bps*.

If the D-ASA has zero or undefined coupons (`K=0`), the *coupon rates* array **MUST**
be empty and the *interest rate* **MUST** be used instead.

> Coupon rates could be derived from the interest rate.

> 📎 **EXAMPLE**
>
> D-ASA with 4 coupons with the following rates: 2,00%, 2,50%, 3,00%, and 3,50%
> would have the following coupon rates array (bps):
>
> ```text
> uint64[] = [200, 250, 300, 350]
> ```

> 📎 **EXAMPLE**
>
> D-ASA with zero coupons would have the following coupon rates array (bps):
>
> ```text
> uint64[] = []
> ```

The *coupon rates* **MUST** be set using the `asset_config` method.

## Accruing Interest

> Debt instruments may accrue interest over time.

The D-ASA *units* **MAY** accrue interest \\([IPAC]\\), according to the *day-count
convention* (see [Day-Count Convention](./day-count-convention.md) section).

If the D-ASA has coupons, the *units* accrued interest **MUST** be calculated with
respect to the latest coupon due date.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with `4` coupons. The 2nd coupon is due. The D-ASA units are
> accruing the interest of the 3rd coupon. The accrued interest is calculated according
> to the day-count convention, applied to the elapsed time with respect to the 2nd
> coupon due date.

If the D-ASA has coupons, the account *units* accrued interest calculation **SHOULD**
fail if it has pending coupon payments.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with `4` coupons. The 2nd coupon is due. The D-ASA units are
> accruing the interest of the 3rd coupon. Coupon payments are not executed synchronously
> for all the Investors. The 2nd coupon payment is executed for Investor A, while
> Investor B is still waiting for the payment settlement. The accrued interest calculation
> succeeds for Investor A and fails for Investor B until the 2nd coupon payment is
> settled.
