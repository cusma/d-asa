# Set Early Repayment Time Events

```json
{{#include ./include/interface.set-early-repayment-time-events.json}}
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

The call **MUST** fail with the `INVALID_EARLY_REPAYMENT_EDN_DATE` error code if
the *early repayment end date* is later than the *maturity date*.

The call **MUST** fail with the `INVALID_PAST_EVENT` error code if a past event
is modified.
