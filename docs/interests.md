# Interests {#interests}

> Debt instruments interest is calculated on a fixed or variable rate on the outstanding
> principal.

> The interest rate is the nominal yield paid by the debt instrument on the principal,
> usually expressed as *Annual Percentage Yield* (APY).

The D-ASA *interest rates* **MUST** be defined in *<a href="https://en.wikipedia.org/wiki/Basis_point">basis
points</a>* (*bps*).

## Interest Rate {#interest-rate}

The D-ASA **MUST** define an *interest rate* (`uint16`).

## Coupons {#coupons}

> Debt instruments can pay interest in periodic installments, called coupons.

> Coupons mature in a coupon period, according to a defined coupon schedule.

The D-ASA **MUST** define the number of *total coupons* `K` (`uint64`):

- `K>0` if the D-ASA has a **defined** number of coupons;
- `K=0` if the D-ASA has **zero** or **undefined** (perpetual) coupons.

## Coupon Rates {#coupon-rates}

> Debt instruments can pay coupons with fixed or variable interest rates.

The D-ASA **MAY** define the *coupon rates* as `uint16[]` array, where:

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

## Variable Rates {#variable-rates}

The *interest rate* **MAY** be updated using the **OPTIONAL** `update_interest_rate`
method.

The *coupon rates* **MAY** be updated using the **OPTIONAL** `update_coupon_rates`
method.

The updated *coupon rates* **MUST NOT** modify past coupon rates.

> A reference implementation **SHOULD** properly restrict the coupon rate updatability.

> 📎 **EXAMPLE**
>
> A D-ASA has variable interest rates pegged to an off-chain index. Interest update
> permissions are granted to an external interest oracle.

> 📎 **EXAMPLE**
>
> A D-ASA has variable interest rates based on covenant breaches. Interest update
> permissions are granted to a trustee in charge of verifying breaches.

## Accruing Interest {#accruing-interest}

> Debt instruments may accrue interest over time.

The D-ASA *units* **MAY** accrue interest, according to the *day-count convention*
(see [Day-Count Convention](./day-count-convention.md) section).
