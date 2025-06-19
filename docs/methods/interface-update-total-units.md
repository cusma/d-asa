# Update Total Units

```json
{{#include ../.include/interface.update-total-units.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset is suspended.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
any due coupon still to be paid.
