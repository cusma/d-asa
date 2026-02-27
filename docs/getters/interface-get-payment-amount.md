# Get Payment Amount

```json
{
  "name": "get_payment_amount",
  "desc": "Get the next payment amount",
  "readonly": true,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    }
  ],
  "returns": {
    "type": "(uint64,uint64)",
    "desc": "Interest amount in denomination asset, Principal amount in denomination asset"
  },
  "errors": [
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid Holding Address"
    }
  ]
}
```

The getter **MUST** return the next payment amount for the account or `0` if there
is no payment to execute for the account.

The getter **MUST** return the interest and the principal components separately.

{{#include ../.include/styles.md:example}}
> Let's have a D-ASA with `4` coupons. The account already received `2` coupon payments.
> The getter returns the interest amount of the 3rd coupon.

{{#include ../.include/styles.md:example}}
> Let's have a D-ASA with `4` coupons and a principal amortizing schedule. The account
> already received `2` coupon payments. The getter returns the interest amount of
> the 3rd coupon and the amortized principal.

{{#include ../.include/styles.md:example}}
> Let's have a D-ASA with `4` coupons and principal at maturity. The account already
> received `4` coupon payments. The getter returns the amount of the principal repayment.

{{#include ../.include/styles.md:example}}
> Let's have a D-ASA with zero coupons and principal at maturity. The principal
> is not yet mature. The getter returns the amount of the principal repayment.

{{#include ../.include/styles.md:example}}
> Let's have a D-ASA with perpetual coupons and no callable principal. The account
> already received `N` coupon payments. The getter returns the interest amount of
> the `N+1` coupon.
