# Asset Config

```json
{{#include ./include/interface.asset-config.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `ALREADY_CONFIGURED` error code if the D-ASA has
been already configured.

The call **MUST** fail with the `INVALID_MINIMUM_DENOMINATION` error code if the
*minimum denomination* is not a divisor of the *principal*.

The call **MUST** fail with the `INVALID_DAY_COUNT_CONVENTION` error code if the
*day-count convention* ID is invalid.

The call **MUST** fail with the `INVALID_TIME_EVENTS_LENGTH` error code if the length
of the *time events* is not greater than or equal to:

- *total coupons* + `3`, if the D-ASA **has not** a defined *maturity date*;
- *total coupons* + `4`, if the D-ASA **has** a defined *maturity date*.

The call **MUST** fail with the `INVALID_TIME` error code if the first *time event*
is earlier than the latest timestamp (or block height).

The call **MUST** fail with the `INVALID_SORTING` error code if the *time events*
are not sorted in strictly ascending order.

The call **MUST** fail with the `INVALID_TIME_PERIOD_DURATION` error code if the
*time period durations* are not strictly greater than zero.
