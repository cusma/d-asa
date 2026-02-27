# Update Time Periods

```json
{
  "name": "update_time_periods",
  "desc": "Update D-ASA variable time periods",
  "readonly": false,
  "args": [
    {
      "type": "(uint64,uint64)[]",
      "name": "time_periods",
      "desc": "D-ASA time periods"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the update"
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
      "code": "INVALID_TIME_PERIOD",
      "message": "Time period durations must be greater than zero"
    },
    {
      "code": "PENDING_COUPON_PAYMENT",
      "message": "Pending due coupon payment"
    }
  ]
}

```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset is suspended.

The call **MUST** fail with the `INVALID_TIME_PERIOD` error code if the *time period
durations* are not strictly greater than zero.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
any due coupon still to be paid.
