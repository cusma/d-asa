# Secondary Market {#secondary-market}

> Debt instruments can be traded on secondary markets.

Secondary-market control is an execution-layer policy.

## Transfer window

If transfer window enforcement is required, the Arranger **MUST** configure it with
`transfer_set_schedule(open_date, closure_date)`.

The transfer window is interpreted as:

```text
open_date <= now < closure_date
```

The method **MUST** reject a schedule in which `open_date >= closure_date`.

## Default behavior

If no transfer window is configured, the current reference implementation applies
no additional secondary-market date restriction beyond the generic transfer checks.

## Relation to normalization

The SDK normalization helpers may carry secondary-market dates as deployment metadata.
Those dates are not part of the on-chain `NormalizedActusTerms` ABI struct in the
current kernel. On-chain enforcement therefore happens through `transfer_set_schedule`,
not through `contract_config`.
