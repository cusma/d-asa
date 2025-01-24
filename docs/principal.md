# Principal (Par) {#principal-(par)}

> Debt instruments principal is the amount of capital borrowed and used as a base
> for calculating interest.

The D-ASA **MAY** define the *principal* \\([NT]\\) (`uint64`)*,* expressed in the
*denomination asset*.

If the D-ASA has a *principal*, it **MUST** define a *minimum denomination* (`uint64`),
expressed in the *denomination asset*.

The *minimum denomination* **MUST** be a divisor of the *principal*.

The *principal* and the *minimum denomination* **MUST** be set using the `asset_config`
method.

If the D-ASA has no defined *principal*, the *principal* and the *minimum denomination*
**MUST** be set to `0`.

## Amortization

If the debt instrument has *principal amortization*, the D-ASA **MUST** define the
*amortization rates* as `uint16[]` array, where:

- The length of the array is `N=K+1`, with `K` equal to the **fixed** *total coupons*;

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
