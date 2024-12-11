# Get Payment Amount

```json
{{#include ./include/interface.get-payment-amount.json}}
```

If the D-ASA has coupons, the *payment index* **MUST** be `1 <= payment index <=
total coupons + 1`.

If the D-ASA has zero coupon, the *payment index* **MUST** be `1` (corresponding
to the principal payment).
