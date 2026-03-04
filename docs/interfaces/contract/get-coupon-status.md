# Get Coupons Status

```json
{
  "name": "get_coupons_status",
  "desc": "Get D-ASA coupons status",
  "readonly": true,
  "args": [],
  "returns": {
    "type": "(uint64,uint64,uint64,(uint64,uint64),bool)",
    "desc": "Total coupons, Due coupons, Next coupon due date, (Day count factor numerator, Day count factor denominator) , All coupons due paid"
  }
}
```

The *next coupon due date* value **MUST** be `0` if all coupons are due.

The *day count factor* values **MUST** `0` if the method is called before the *issuance
date* or if all coupons are due.
