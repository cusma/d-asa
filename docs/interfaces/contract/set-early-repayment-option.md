# Set Early Repayment Option

```json
{
  "name": "set_early_repayment_option",
  "desc": "Set early repayment schedule and eventual penalty rate",
  "readonly": false,
  "args": [
    {
      "type": "uint64[]",
      "name": "time_events",
      "desc": "Early repayment time events (strictly ascending order)"
    },
    {
      "type": "uint64",
      "name": "penalty_rate",
      "desc": "Early repayment penalty rate (absolute or relative), if any"
    }
  ],
  "returns": {
    "type": "(uint64, uint64)",
    "desc": "Early repayments start date, Early repayments end date"
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
      "code": "INVALID_EARLY_REPAYMENT_START_DATE",
      "message": "Invalid early repayment start date"
    },
    {
      "code": "INVALID_EARLY_REPAYMENT_END_DATE",
      "message": "Invalid early repayment end date"
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
of the *time events* is not greater than or equal to `2`.

The call **MUST** fail with the `INVALID_SORTING` error code if the *time events*
are not sorted in strictly ascending order.

The call **MUST** fail with the `INVALID_EARLY_REPAYMENT_START_DATE` error code
if the *early repayment start date* is earlier than the *issuance date*.

The call **MUST** fail with the `INVALID_EARLY_REPAYMENT_END_DATE` error code if
the *early repayment end date* is later than the *maturity date*.

The call **MUST** fail with the `INVALID_PAST_EVENT` error code if a past event
is modified.
