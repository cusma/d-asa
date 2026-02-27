# Update Time Events

```json
{
  "name": "update_time_events",
  "desc": "Update D-ASA variable time schedule",
  "readonly": false,
  "args": [
    {
      "type": "uint64[]",
      "name": "time_events",
      "desc": "D-ASA time events (strictly ascending order)"
    }
  ],
  "returns": {
    "type": "(uint64, uint64, uint64, uint64, uint64)",
    "desc": "Primary distribution opening date, Primary distribution closure date, Issuance date, Maturity date, Timestamp of the update"
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
      "code": "INVALID_TIME_EVENTS_LENGTH",
      "message": "Time events length is invalid"
    },
    {
      "code": "INVALID_TIME",
      "message": "Time events must be set in the future"
    },
    {
      "code": "INVALID_SORTING",
      "message": "Time events are not sorted correctly"
    },
    {
      "code": "INVALID_PAST_EVENT",
      "message": "Past time events can not be modified"
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

The call **MUST** fail with the `INVALID_TIME_EVENTS_LENGTH` error code if the length
of the *time events* is not equal to *total\_coupons* plus `4`.

The call **MUST** fail with the `INVALID_TIME` error code if the first *time event*
is earlier than the latest timestamp (or block height).

The call **MUST** fail with the `INVALID_SORTING` error code if the *time events*
are not sorted in strictly ascending order.

The call **MUST** fail with the `INVALID_PAST_EVENT` error code if a past event
is modified.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
any due coupon still to be paid.
