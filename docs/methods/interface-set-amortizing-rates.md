# Set Amortizing Rates

```json
{
  "name": "set_amortizing_rates",
  "desc": "Set principal amortizing rates",
  "readonly": false,
  "args": [
    {
      "type": "uint64[]",
      "name": "amortizing_rates",
      "desc": "Principal amortizing rates in bps"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the set rates"
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
      "code": "INVALID_AMORTIZING_RATES_LENGTH",
      "message": "Amortizing rates length is invalid"
    },
    {
      "code": "INVALID_RATES",
      "message": "Sum of amortizing rates must be equal to 10000 bps"
    },
    {
      "code": "INVALID_PAST_RATE",
      "message": "Past amortizing rates can not be modified"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `INVALID_AMORTIZING_RATES_LENGTH` error code if
the length of the *amortizing rates* is not equal to *total\_coupons* plus `1`.

The call **MUST** fail with the `INVALID_RATES` error code if the sum of *amortizing
rates* is not equal to 10,000 bps.

The call **MUST** fail with the `INVALID_PAST_RATE` error code if a past amortizing
rate is modified.
