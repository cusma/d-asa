# ACTUS Kernel Interface

The ACTUS Kernel interface configures the normalized contract, stores the execution
schedule, and advances non-cash lifecycle events.

## `contract_create`

```json
{
  "name": "contract_create",
  "create": "require",
  "readonly": false,
  "args": [
    { "name": "arranger", "type": "address" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of contract creation" },
  "errors": []
}
```

## `contract_config`

```json
{
  "name": "contract_config",
  "readonly": false,
  "args": [
    { "name": "terms", "type": "NormalizedActusTerms" },
    { "name": "initial_state", "type": "InitialKernelState" },
    { "name": "prospectus", "type": "Prospectus" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of contract configuration" },
  "errors": [
    "UNAUTHORIZED",
    "ALREADY_CONFIGURED",
    "INVALID_ACTUS_CONFIG",
    "INVALID_DAY_COUNT_CONVENTION",
    "INVALID_DENOMINATION",
    "INVALID_SETTLEMENT_ASSET",
    "INVALID_IED"
  ]
}
```

Only the Arranger may call this method.

## `contract_schedule`

```json
{
  "name": "contract_schedule",
  "readonly": false,
  "args": [
    { "name": "schedule_page_index", "type": "uint64" },
    { "name": "is_last_page", "type": "bool" },
    { "name": "schedule_page", "type": "ExecutionSchedulePage" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the schedule upload" },
  "errors": [
    "UNAUTHORIZED",
    "ALREADY_CONFIGURED",
    "TERMS_NOT_CONFIGURED",
    "INVALID_SCHEDULE_PAGE",
    "INVALID_EVENT_ID",
    "INVALID_ACTUS_CONFIG",
    "INVALID_SORTING"
  ]
}
```

Only the Arranger may call this method.

## `contract_execute_ied`

```json
{
  "name": "contract_execute_ied",
  "readonly": false,
  "args": [],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the IED execution" },
  "errors": [
    "NOT_CONFIGURED",
    "UNAUTHORIZED",
    "DEFAULTED",
    "SUSPENDED",
    "INVALID_EVENT_CURSOR",
    "INVALID_EVENT_TYPE",
    "NO_DUE_CASHFLOW",
    "INVALID_ACTUS_CONFIG",
    "PRIMARY_DISTRIBUTION_INCOMPLETE"
  ]
}
```

Only the Arranger may call this method.

## `apply_non_cash_event`

```json
{
  "name": "apply_non_cash_event",
  "readonly": false,
  "args": [
    { "name": "event_id", "type": "uint64" },
    { "name": "payload", "type": "ObservedEventRequest" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the event application" },
  "errors": [
    "NOT_CONFIGURED",
    "DEFAULTED",
    "SUSPENDED",
    "OBSERVED_EVENT_REQUIRED",
    "UNAUTHORIZED",
    "INVALID_EVENT_ID",
    "INVALID_EVENT_CURSOR",
    "INVALID_EVENT_TYPE",
    "INVALID_SCHEDULE_PAGE",
    "INVALID_ACTUS_CONFIG",
    "INVALID_SORTING",
    "NO_DUE_CASHFLOW",
    "PENDING_IED"
  ]
}
```

`RR` and `RRF` execution is Observer-controlled. Other non-cash events are Arranger-controlled.

## `append_observed_cash_event`

```json
{
  "name": "append_observed_cash_event",
  "readonly": false,
  "args": [
    { "name": "payload", "type": "ObservedCashEventRequest" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the append operation" },
  "errors": [
    "NOT_CONFIGURED",
    "UNAUTHORIZED",
    "DEFAULTED",
    "SUSPENDED",
    "PENDING_IED",
    "OBSERVED_EVENT_REQUIRED",
    "INVALID_EVENT_ID",
    "INVALID_EVENT_TYPE",
    "INVALID_SCHEDULE_PAGE",
    "INVALID_ACTUS_CONFIG",
    "INVALID_SORTING"
  ]
}
```

## `contract_get_state`

```json
{
  "name": "contract_get_state",
  "readonly": true,
  "args": [],
  "returns": { "type": "KernelState", "desc": "Current kernel state snapshot" },
  "errors": ["NOT_CONFIGURED"]
}
```

## `contract_get_next_due_event`

```json
{
  "name": "contract_get_next_due_event",
  "readonly": true,
  "args": [],
  "returns": {
    "type": "ExecutionScheduleEntry",
    "desc": "Next due schedule entry, or a zero sentinel if the contract ended"
  },
  "errors": ["NOT_CONFIGURED"]
}
```
