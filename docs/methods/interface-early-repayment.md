# Early Repayment

```json
{
  "name": "early_repayment",
  "desc": "Pay the principal to an account before maturity",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "uint64",
      "name": "units",
      "desc": "Amount of D-ASA units to repay"
    },
    {
      "type": "byte[]",
      "name": "payment_info",
      "desc": "Additional payment information (Optional)"
    }
  ],
  "returns": {
    "type": "(uint64, uint64, byte[])",
    "desc": "Paid principal amount in denomination asset, Payment timestamp, Payment information"
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
      "code": "PENDING_COUPON_PAYMENT",
      "message": "Pending due coupon payment for the account"
    },
    {
      "code": "ZERO_UNITS",
      "message": "Can not repay zero units"
    },
    {
      "code": "OVER_REPAYMENT",
      "message": "Insufficient units to repay for the account"
    },
    {
      "code": "ALREADY_MATURE",
      "message": "Already mature"
    }
  ]
}
```

The call **MUST** remove D-ASA early rapid units from the Account Holding Address
and from circulation.

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `SUSPENDED` error code if the asset operations or
any account involved in the transfers are suspended.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `NO_UNTIS` error code if the Account has no D-ASA
units.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
a due coupon still to be paid for the Account.

The call **MUST** fail with the `ZERO_UNITS` error code if the distributing units
are null.

The call **MUST** fail with the `OVER_REPAYMENT` error code if there are no sufficient
remaining D-ASA units to repay.

The call **MUST** fail with the `ALREADY_MATURE` error code if the principal is
mature.

If the D-ASA has on-chain payment agent, the call **MUST** fail with the `NOT_ENOUGH_FUNDS`
error code if funds are not enough for the payment.
