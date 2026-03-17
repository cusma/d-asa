# Payment Agent Interface

The Payment Agent interface funds due ACTUS cash events and allows holder claims.

## `fund_due_cashflows`

```json
{
  "name": "fund_due_cashflows",
  "readonly": false,
  "args": [
    { "name": "max_event_count", "type": "uint64" }
  ],
  "returns": { "type": "CashFundingResult", "desc": "Funding result for the processed events" },
  "errors": [
    "NOT_CONFIGURED",
    "UNAUTHORIZED",
    "DEFAULTED",
    "SUSPENDED",
    "PENDING_IED",
    "NO_DUE_CASHFLOW",
    "NOT_ENOUGH_FUNDS"
  ]
}
```

If an Op Daemon is configured, only the Arranger or Op Daemon may call this
method. Otherwise the method is permissionless.

## `claim_due_cashflows`

```json
{
  "name": "claim_due_cashflows",
  "readonly": false,
  "args": [
    { "name": "holding_address", "type": "address" },
    { "name": "payment_info", "type": "byte[]" }
  ],
  "returns": { "type": "CashClaimResult", "desc": "Holder claim result" },
  "errors": [
    "NOT_CONFIGURED",
    "INVALID_HOLDING_ADDRESS",
    "UNAUTHORIZED",
    "DEFAULTED",
    "SUSPENDED",
    "PENDING_IED",
    "NO_DUE_CASHFLOW",
    "NOT_ENOUGH_FUNDS"
  ]
}
```

If the holder's payment path is not executable, the method reports the claimable
amounts without clearing them.
