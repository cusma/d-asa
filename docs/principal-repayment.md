# Principal Repayment {#principal-repayment}

> Debt instruments repay the principal according to the repayment schedule.

The *principal* **MUST** be repaid according to a *principal repayment schedule*.

If the D-ASA has coupons, the *principal* **MUST NOT** be paid if there is any due
coupon still to be paid.

In the case of an on-chain payment agent, the D-ASA **MUST** repay the *principal*
to the Investor’s Payment Addresses.

## Bullet Schedule

If the *principal repayment schedule* is *bullet*, the principal **MUST** be paid
entirely at the *maturity date* using the `pay_principal` method.

## Amortizing Schedule

If *principal repayment schedule* is *amortizing*, the D-ASA **MUST** define the
*amortization rates* as `uint16[]` array, where:

- The length of the array is `N=K+1`, with `K` equal to the *total coupons*;

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

The *principal* **MUST** be repaid along with *coupons*, according to the *amortizing
rates*, using the `pay_coupon` method.

The D-ASA *unit value* **MUST** be updated according to the *outstanding principal.*

It is **RECOMMENDED** to use an ACTUS *interest calculation base* \\([IPCB]\\).

> A reference implementation **SHOULD** calculate interest on the outstanding principal.

> A reference implementation **SHOULD** restrict the amortizing rates updatability.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a *principal* of 1M EUR and a *minimum
> denomination* of 1,000 EUR, 5 coupons, and an even amortizing schedule (20% amortizing
> rate). The D-ASA has 1,000 *total units*. The D-ASA initial *unit value* is 1,000
> EUR. The 1st coupon pays both the interest (according to the *coupon rates*) and
> 20% of the principal (according to *amortizing rates*). The D-ASA outstanding
> principal is 800k EUR. The D-ASA *unit value* is 800 EUR.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a *principal* of 1M EUR and a *minimum
> denomination* of 1,000 EUR. The D-ASA originally had 1,000 *total units* (worth
> 1,000 EUR each) in circulation. A partial repayment of 500k EUR (50% of the original
> principal) must be executed pro rata to all lenders. A single amortizing rate
> of 5,000 bps is used. After the partial repayment, the D-ASA still has 1000 circulating
> units (worth 500 EUR each).
