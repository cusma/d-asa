# Account Governance Suspension

```json
{
  "name": "account_gov_suspension",
  "desc": "Set account suspension status",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "bool",
      "name": "suspended",
      "desc": "Suspension status"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the set account suspension status"
  },
  "errors": [
    {
      "code": "UNAUTHORIZED",
      "message": "Not authorized"
    },
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid account holding address"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.
