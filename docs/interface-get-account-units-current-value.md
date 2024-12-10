# Get Current Account Units Current Value

```json
{{#include ./include/interface.get-account-units-current-value.json}}
```

The call **MUST** fail with the `NO_PRIMARY_DISTRIBUTION` error code if the method
is called before the *primary distribution opening date*.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `INVALID_UNTIS` error code if the *unit* value is
greater than Account D-ASA units.

The *accrued interest* **MUST** `0` if the method is called before the *issuance
date*.

If the D-ASA has coupons, the *accrued interest* **MUST** be `0` after all coupons
are due.

If the D-ASA has zero coupon, the *accrued interest* **MUST** be `0` after the *maturity
date*.