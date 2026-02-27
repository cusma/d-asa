# Get Account Units Current Value

```json
{
  "name": "get_account_units_current_value",
  "desc": "Get account's current units value and accrued interest",
  "readonly": true,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "uint64",
      "name": "units",
      "desc": "Account's units for the current value calculation"
    }
  ],
  "returns": {
    "type": "(uint64,uint64,(uint64,uint64))",
    "desc": "Units current value in denomination asset, Accrued interest in denomination asset, (Day count factor numerator, Day count factor denominator)"
  },
  "errors": [
    {
      "code": "NO_PRIMARY_DISTRIBUTION",
      "message": "Primary distribution not yet executed"
    },
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid Holding Address"
    },
    {
      "code": "INVALID_UNITS",
      "message": "Invalid amount of units for the account"
    },
    {
      "code": "PENDING_COUPON_PAYMENT",
      "message": "Pending due coupon payment for the account"
    }
  ]
}
```

The call **MUST** fail with the `NO_PRIMARY_DISTRIBUTION` error code if the method
is called before the *primary distribution opening date*.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `INVALID_UNTIS` error code if the *unit* value is
greater than Account D-ASA units.

If the D-ASA has coupons, the call **MUST** fail with the `PENDING_COUPON_PAYMENT`
error code if there is an old due coupon still to be paid to any account.

The *accrued interest* **MUST** `0` if the method is called before the *issuance
date*.

If the D-ASA has fixed coupons, the *accrued interest* **MUST** be `0` after all
coupons are due.

If the D-ASA has zero coupons, the *accrued interest* **MUST** be `0` after the
*maturity date*.
