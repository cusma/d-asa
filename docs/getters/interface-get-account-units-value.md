# Get Account Units Value

```json
{
  "name": "get_account_units_value",
  "desc": "Get account's units nominal value",
  "readonly": true,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "uint64",
      "name": "units",
      "desc": "Account's units for the nominal value calculation"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Units nominal value in denomination asset"
  },
  "errors": [
    {
      "code": "NO_PRIMARY_DISTRIBUTION",
      "message": "Primary distribution not yet executed"
    },
    {
      "code": "INVALID_HOLDING_ADDRESS",
      "message": "Invalid Holding Address"
    },
    {
      "code": "INVALID_UNITS",
      "message": "Invalid amount of units for the account"
    }
  ]
}
```

The call **MUST** fail with the `NO_PRIMARY_DISTRIBUTION` error code if the method
is called before the *primary distribution opening date*.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `INVALID_UNITS` error code if the *unit* value is
greater than Account D-ASA units.
