# Set Secondary Time Events

```json
{
  "name": "set_secondary_time_events",
  "desc": "Set secondary market time schedule",
  "readonly": false,
  "args": [
    {
      "type": "uint64[]",
      "name": "secondary_market_time_events",
      "desc": "Secondary market time events (strictly ascending order)"
    }
  ],
  "returns": {
    "type": "(uint64, uint64)",
    "desc": "Secondary market opening date, Secondary market closure date"
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
      "code": "INVALID_SORTING",
      "message": "Time events are not sorted correctly"
    },
    {
      "code": "INVALID_SECONDARY_OPENING_DATE",
      "message": "Invalid secondary market opening date"
    },
    {
      "code": "INVALID_SECONDARY_CLOSURE_DATE",
      "message": "Invalid secondary market closure date"
    },
    {
      "code": "INVALID_PAST_EVENT",
      "message": "Past time events can not be modified"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `INVALID_TIME_EVENTS_LENGTH` error code if the length
of the *time events* is not greater than or equal to `1`.

The call **MUST** fail with the `INVALID_SORTING` error code if the *time events*
are not sorted in strictly ascending order.

The call **MUST** fail with the `INVALID_SECONDARY_OPENING_DATE` error code if the
*secondary market opening date* is earlier than the *issuance date*.

The call **MUST** fail with the `INVALID_SECONDARY_CLOSURE_DATE` error code if the
*secondary market closure date* is earlier than the *secondary market opening date*
or later than the *maturity date*.

The call **MUST** fail with the `INVALID_PAST_EVENT` error code if a past event
is modified.
