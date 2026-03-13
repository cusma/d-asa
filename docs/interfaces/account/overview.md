# Accounting Interface

The Accounting interface manages holder positions and account-level suspension.

## `account_suspension`

```json
{
  "name": "account_suspension",
  "readonly": false,
  "args": [
    { "name": "holding_address", "type": "address" },
    { "name": "suspended", "type": "bool" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the suspension update" },
  "errors": ["UNAUTHORIZED", "INVALID_HOLDING_ADDRESS"]
}
```

Only an active Authority may call this method.

## `account_open`

```json
{
  "name": "account_open",
  "readonly": false,
  "args": [
    { "name": "holding_address", "type": "address" },
    { "name": "payment_address", "type": "address" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the account opening" },
  "errors": ["UNAUTHORIZED", "DEFAULTED", "SUSPENDED", "INVALID_HOLDING_ADDRESS"]
}
```

Only an active Account Manager may call this method.

The current implementation treats an already existing holding address as `INVALID_HOLDING_ADDRESS`.

## `account_update_payment_address`

```json
{
  "name": "account_update_payment_address",
  "readonly": false,
  "args": [
    { "name": "holding_address", "type": "address" },
    { "name": "payment_address", "type": "address" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the account update" },
  "errors": ["UNAUTHORIZED", "DEFAULTED", "SUSPENDED", "INVALID_HOLDING_ADDRESS"]
}
```

Only the Account Holding Address itself may call this method.

## `account_get_position`

```json
{
  "name": "account_get_position",
  "readonly": true,
  "args": [
    { "name": "holding_address", "type": "address" }
  ],
  "returns": { "type": "AccountPosition", "desc": "Full holder accounting position" },
  "errors": ["INVALID_HOLDING_ADDRESS"]
}
```
