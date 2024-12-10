# Get Coupons Status

```json
{{#include ./include/interface.get-coupon-status.json}}
```

The *next coupon due date* value **MUST** be `0` if all coupons are due.

The *day count factor* values **MUST** `0` if the method is called before the *issuance
date* or if all coupons are due.
