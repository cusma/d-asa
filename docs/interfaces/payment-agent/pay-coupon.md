# Pay Coupon

```json
{
  "name": "pay_coupon",
  "desc": "Pay due coupon to an account",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "byte[]",
      "name": "payment_info",
      "desc": "Additional payment information (Optional)"
    }
  ],
  "returns": {
    "type": "(uint64, uint64, byte[])",
    "desc": "Paid coupon amount in denomination asset, Payment timestamp, Payment context"
  },
  "errors": [
    {
      "code": "UNAUTHORIZED",
      "message": "Not authorized"
    },
    {
      "code": "DEFAULTED",
      "message": "Defaulted"
    },
    {
      "code": "SUSPENDED",
      "message": "Suspended operations"
    },
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid account holding address"
    },
    {
      "code": "NO_UNITS",
      "message": "No D-ASA units"
    },
    {
      "code": "NO_DUE_COUPON",
      "message": "No due coupon to pay"
    },
    {
      "code": "PENDING_COUPON_PAYMENT",
      "message": "Pending due coupon payment"
    },
    {
      "code": "NOT_ENOUGH_FUNDS",
      "message": "Not enough funds for the payment"
    }
  ]
}
```

> A reference implementation **SHOULD NOT** require an authorized caller.

If the D-ASA has an amortizing principal payment schedule, the call **MUST** update
the Account's *unit value*.

If the call requires authorization, it **MUST** fail with the `UNAUTHORIZED` error
code if not called by an authorized caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.

The call **MUST** fail with the `NO_UNITS` error code if the Account has no D-ASA
units.

The call **MUST** fail with the `NO_DUE_COUPON` error code if there is no due
coupon left to pay for the Account.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
an old due coupon still to be paid to any account.

If the D-ASA has on-chain payment agent, the call **MUST** fail with the `NOT_ENOUGH_FUNDS`
error code if funds are not enough for the payment.
