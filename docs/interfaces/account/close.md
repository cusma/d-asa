# Account Close

```json
{
  "name": "account_close",
  "desc": "Close D-ASA account",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    }
  ],
  "returns": {
    "type": "(uint64,uint64)",
    "desc": "Closed units, Timestamp of the account closing"
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
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid account holding address"
    }
  ]
}

```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller or if the operation is not authorized.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.
