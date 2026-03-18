# Transfer Agent Interface

The Transfer Agent interface manages transfer windows, primary allocations, and
secondary transfers.

## `transfer_set_schedule`

```json
{
  "name": "transfer_set_schedule",
  "readonly": false,
  "args": [
    { "name": "open_date", "type": "uint64" },
    { "name": "closure_date", "type": "uint64" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the schedule update" },
  "errors": ["UNAUTHORIZED", "INVALID_SORTING", "INVALID_TRANSFER_OPENING"]
}
```

Only the Arranger may call this method. The `IED` **MUST** be already defined and
the opening date **MUST** be greater than or equal to `IED`.

## `primary_distribution`

```json
{
  "name": "primary_distribution",
  "readonly": false,
  "args": [
    { "name": "holding_address", "type": "address" },
    { "name": "units", "type": "uint64" }
  ],
  "returns": { "type": "uint64", "desc": "Remaining undistributed unit balance" },
  "errors": [
    "NOT_CONFIGURED",
    "UNAUTHORIZED",
    "DEFAULTED",
    "SUSPENDED",
    "PRIMARY_DISTRIBUTION_CLOSED",
    "INVALID_HOLDING_ADDRESS",
    "ZERO_UNITS",
    "OVER_DISTRIBUTION"
  ]
}
```

## `transfer`

```json
{
  "name": "transfer",
  "readonly": false,
  "args": [
    { "name": "sender_holding_address", "type": "address" },
    { "name": "receiver_holding_address", "type": "address" },
    { "name": "units", "type": "uint64" }
  ],
  "returns": { "type": "uint64", "desc": "Number of units transferred" },
  "errors": [
    "NOT_CONFIGURED",
    "DEFAULTED",
    "SUSPENDED",
    "PENDING_IED",
    "CLOSED_TRANSFER",
    "UNAUTHORIZED",
    "INVALID_HOLDING_ADDRESS",
    "SELF_TRANSFER",
    "NULL_TRANSFER",
    "OVER_TRANSFER",
    "PENDING_ACTUS_EVENT"
  ]
}
```

The current implementation requires the sender holding address to submit the transaction.
