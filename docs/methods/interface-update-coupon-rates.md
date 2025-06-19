# Update Coupon Rates

```json
{{#include ../.include/interface.update-coupon-rates.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset is suspended.

The call **MUST** fail with the `INVALID_COUPON_RATES_LENGTH` error code if the
length of the *coupon rates* is not equal to *total_coupons*.

The call **MUST** fail with the `INVALID_PAST_RATE` error code if a due coupon rate
is modified.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
any due coupon still to be paid.
