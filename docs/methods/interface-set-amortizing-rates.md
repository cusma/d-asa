# Set Amortizing Rates

```json
{{#include ../.include/interface.set-amortizing-rates.json}}
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
