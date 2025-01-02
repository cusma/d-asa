# Get Payment Amount

```json
{{#include ./include/interface.get-payment-amount.json}}
```

The getter **MUST** return the next payment amount for the account or `0` if there
is no payment to execute for the account.

The getter **MUST** return the interest and the principal components separately.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with `4` coupons. The account already received `2` coupon payments.
> The getter returns the interest amount of the 3rd coupon.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with `4` coupons and a principal amortizing schedule. The account
> already received `2` coupon payments. The getter returns the interest amount of
> the 3rd coupon and the amortized principal.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with `4` coupons and principal at maturity. The account already
> received `4` coupon payments. The getter returns the amount of the principal repayment.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with zero coupons and principal at maturity. The principal
> is not yet mature. The getter returns the amount of the principal repayment.

> 📎 **EXAMPLE**
>
> Let's have a D-ASA with perpetual coupons and no callable principal. The account
> already received `N` coupon payments. The getter returns the interest amount of
> the `N+1` coupon.
