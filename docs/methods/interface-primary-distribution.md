# Primary Distribution

```json
{
  "name": "primary_distribution",
  "desc": "Distribute D-ASA units to accounts according the primary market",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "holding_address",
      "desc": "Account Holding Address"
    },
    {
      "type": "uint64",
      "name": "units",
      "desc": "Amount of D-ASA units to distribute"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Remaining D-ASA units to be distributed"
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
    },
    {
      "code": "ZERO_UNITS",
      "message": "Cannot distribute zero units"
    },
    {
      "code": "OVER_DISTRIBUTION",
      "message": "Insufficient remaining D-ASA units"
    },
    {
      "code": "PRIMARY_DISTRIBUTION_CLOSED",
      "message": "Primary distribution is closed"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by the authorized
primary market entity.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
associated with the holding address does not exist.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `ZERO_UNITS` error code if the distributing units
are null.

The call **MUST** fail with the `OVER_DISTRIBUTION` error code if there are no sufficient
remaining D-ASA units for the primary distribution.

The call **MUST** fail with the `PRIMARY_DISTRIBUTION_CLOSED` error code if the
*primary distribution* is closed.
