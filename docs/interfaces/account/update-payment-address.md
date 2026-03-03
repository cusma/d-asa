# Update Payment Address

```json
{
  "name": "update_payment_address",
  "desc": "Update Payment Address of an account",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "address",
      "name": "payment_address",
      "desc": "Account Payment Address"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the account update"
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
      "message": "Suspended operations"
    },
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid account holding address"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by the Holding
Address.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.
