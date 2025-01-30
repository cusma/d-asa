# Principal {#principal}

> Debt instruments principal is the amount of capital borrowed and used as a base
> for calculating interest.

The D-ASA **MAY** define the *principal* \\([NT]\\) (`uint64`), expressed in the
*denomination asset*.

If the D-ASA has a *principal*, it **MUST** define a *minimum denomination* (`uint64`),
expressed in the *denomination asset*.

The *minimum denomination* **MUST** be a divisor of the *principal*.

The *principal* and the *minimum denomination* **MUST** be set using the `asset_config`
method.

If the D-ASA has no defined *principal*, the *principal* and the *minimum denomination*
**MUST** be set to `0`.

## Discount

> Debt instruments principal may be placed at discount on issuance.

The D-ASA **MAY** define a *discount* rate \\([PDIED]\\) (`uint16`) in *bps* to
apply to the principal on the issuance.

The *discount* **MUST** be set using the `asset_config` method.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a principal of 1M EUR paid at maturity
> and a minimum denomination of 1,000 EUR. The D-ASA has a principal discount of
> 200 bps (2%) at the issuance. Each D-ASA unit is sold on the primary market at
> 980 EUR and will be redeemed for 1,000 EUR of principal at maturity.

## Amortization

> ⚠️This section is still subject to major changes and reviews.

> Debt instruments principal may be amortized until maturity, according to an amortization
> schedule.

If the debt instrument has *principal amortization*, the D-ASA **MUST** define the
*amortization rates* as `uint16[]` array, where:

- The length of the array is `N=K+1`, with `K` equal to the **fixed** *total coupons*
(see [Coupons](./interests.md#coupons) section);

- The first `K`elements of the array are the *amortizing rates* associated with
*coupon* payments;

- The last element of the array is the *amortization rate* associated with *principal*
payment;

- The elements of the array are expressed in *<a href="https://en.wikipedia.org/wiki/Basis_point">basis
points</a>* (*bps*);

- The sum of all the *amortization rates* is equal to `10,000` *bps*.

> 📎 **EXAMPLE**
>
> A D-ASA with 5 coupons and even principal amortizing rates has the following amortizing
> rates (bps):
>
> ```uint64[] = [2000, 2000, 2000, 2000, 2000, 0]```

> 📎 **EXAMPLE**
>
> A D-ASA with 5 coupons and a single principal early repayment of 50% has the following
> amortizing rates (bps):
>
> ```uint64[] = [0, 0, 5000, 0, 0, 5000]```

> 📎 **EXAMPLE**
>
> A D-ASA with 4 coupons and different principal amortizing rates (bps):
>
> ```uint64[] = [1000, 2000, 3000, 4000, 0]```

> 📎 **EXAMPLE**
>
> The following are invalid amortizing rates, since their sum is not equal to `10,000`
> bps:
>
> ```uint64[] = [1000, 2000, 3000, 4000, 5000]```

The *amortizing rates* **MUST** be set using the **OPTIONAL** `set_amortizing_rates`
method.

The *amortizing rates* **MAY** be updated with the **OPTIONAL** `set_amortizing_rates`
method.

The updated *amortizing rates* **MUST NOT** modify past amortizing rates.
