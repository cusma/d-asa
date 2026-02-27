# Asset Config

```json
{
  "name": "asset_config",
  "desc": "Configure the Debt Algorand Standard Application",
  "readonly": false,
  "args": [
    {
      "type": "uint64",
      "name": "denomination_asset_id",
      "desc": "Denomination asset identifier"
    },
    {
      "type": "uint64",
      "name": "settlement_asset_id",
      "desc": "Settlement asset identifier"
    },
    {
      "type": "uint64",
      "name": "principal",
      "desc": "Principal, expressed in denomination asset"
    },
    {
      "type": "uint16",
      "name": "principal_discount",
      "desc": "Discount on principal in bps"
    },
    {
      "type": "uint64",
      "name": "minimum_denomination",
      "desc": "Minimum denomination, expressed in denomination asset"
    },
    {
      "type": "uint8",
      "name": "day_count_convention_id",
      "desc": "Day-count convention for interests calculation"
    },
    {
      "type": "uint16",
      "name": "interest_rate",
      "desc": "Interest rates in bps"
    },
    {
      "type": "uint16[]",
      "name": "coupon_rates",
      "desc": "Coupon interest rates in bps"
    },
    {
      "type": "uint64[]",
      "name": "time_events",
      "desc": "Time events (strictly ascending order)"
    },
    {
      "type": "(uint64,uint64)[]",
      "name": "time_periods",
      "desc": "Time periods of recurring time events"
    }
  ],
  "returns": {
    "type": "void"
  },
  "errors": [
    {
      "code": "UNAUTHORIZED",
      "message": "Not authorized"
    },
    {
      "code": "ALREADY_CONFIGURED",
      "message": "D-ASA already configured"
    },
    {
      "code": "INVALID_MINIMUM_DENOMINATION",
      "message": "Minimum denomination is not a divisor of principal"
    },
    {
      "code": "INVALID_DAY_COUNT_CONVENTION",
      "message": "Invalid day-count convention ID"
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
      "code": "INVALID_TIME_PERIOD_DURATION",
      "message": "Time period durations must be greater than zero"
    },
    {
      "code": "INVALID_SETTLEMENT_ASSET",
      "message": "Different settlement asset not supported, must be equal to denomination asset"
    },
    {
      "code": "INVALID_TIME_PERIODS",
      "message": "Time periods not properly set"
    },
    {
      "code": "INVALID_TIME_PERIOD_REPETITIONS",
      "message": "Time period repetitions not properly set"
    },
    {
      "code": "INVALID_COUPON_RATES",
      "message": "Coupon rates not properly set"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `ALREADY_CONFIGURED` error code if the D-ASA has
been already configured.

The call **MUST** fail with the `INVALID_DENOMINATION` error code if the *denomination
asset* is not properly set for the specific implementation.

The call **MUST** fail with the `INVALID_MINIMUM_DENOMINATION` error code if the
*minimum denomination* is not a divisor of the *principal*.

The call **MUST** fail with the `INVALID_DAY_COUNT_CONVENTION` error code if the
*day-count convention* ID is invalid.

The call **MUST** fail with the `INVALID_INTEREST_RATE` error code if the *interest
rate* is not properly set for the specific implementation.

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

The call **MAY** fail with the `INVALID_SETTLEMENT_ASSET` error code if a *settlement
asset* different from the *denomination asset* is not supported by the specific
implementation.

The call **MAY** fail with the `INVALID_TIME_PERIODS` error code if the *time periods*
are not properly set for the specific implementation.

The call **MAY** fail with the `INVALID_TIME_PERIOD_REPETITIONS` error code if the
*time period repetitions* are not properly set for the specific implementation.

The call **MAY** fail with the `INVALID_COUPON_RATES` error code if the *coupon
rates* are not properly set for the specific implementation.
