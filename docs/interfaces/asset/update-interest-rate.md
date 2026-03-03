# Update Interest Rate

```json
{
  "name": "update_interest_rate",
  "desc": "Update variable interest rates in bps",
  "readonly": false,
  "args": [
    {
      "type": "uint16",
      "name": "interest_rate",
      "desc": "Interest rate in bps"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the update"
  },
  "errors": [
    {
      "code": "UNAUTHORIZED",
      "message": "Not authorized"
    },
    {
      "code": "DEFAULTED",
      "message": "Defaulted"
    },
    {
      "code": "SUSPENDED",
      "message": "Asset operations are suspended"
    },
    {
      "code": "PENDING_COUPON_PAYMENT",
      "message": "Pending due coupon payment"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset is suspended.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
any due coupon still to be paid.
