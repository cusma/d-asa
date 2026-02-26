# Account Get Info

```json
{
  "name": "account_get_info",
  "desc": "Get account account info",
  "readonly": true,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    }
  ],
  "returns": {
    "type": "(address,uint64,uint64,uint64,bool)",
    "desc": "Payment Address, D-ASA units, Unit nominal value in denomination asset, Paid coupons, Suspended"
  },
  "errors": [
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid Holding Address"
    }
  ]
}
```

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.
