# Events

The D-ASA uses two distinct event concepts:

1. *ACTUS schedule events*: contractual events stored in the normalized execution
schedule.

1. *ARC-28 execution events*: proofs that a scheduled event was actually applied
on chain.

Those concepts are related, but they are not interchangeable.

## ACTUS schedule events

ACTUS schedule events live inside `ExecutionScheduleEntry` records in the boxed
schedule. They describe what the contract is expected to execute next.

An ACTUS schedule event contains:

- `event_id`
- `event_type`
- `scheduled_time`
- accrual factors
- next-state values
- flags

Schedule events exist before execution and remain part of contract state even if
no ARC-28 proof has been emitted yet.

See [Kernel State and Schedule](../specs/contract/kernel-state-and-schedule.md)
for the normative schedule definition.

## ARC-28 execution events

When the kernel applies a schedule entry, it emits an ARC-28 `ExecutionEvent` as
an execution proof.

This proof is non-normative receipt data. It does not replace the kernel state,
and it does not define future schedule entries. Its purpose is to attest that a
given event was applied at a specific block time with a specific payoff and settlement
outcome.

The current execution-proof schema is:

```json
{
  "name": "ExecutionEvent",
  "desc": "Non-normative receipt for on-chain execution of a scheduled ACTUS event",
  "args": [
    { "name": "contract_id", "type": "uint64", "desc": "Application ID emitting the proof" },
    { "name": "event_id", "type": "uint64", "desc": "Executed schedule event identifier" },
    { "name": "event_type", "type": "uint8", "desc": "Executed ACTUS event type" },
    { "name": "scheduled_time", "type": "uint64", "desc": "Contractual due timestamp from the schedule" },
    { "name": "applied_at", "type": "uint64", "desc": "Block timestamp at which execution occurred" },
    { "name": "payoff", "type": "uint64", "desc": "Contractual payoff computed for the event" },
    { "name": "payoff_sign", "type": "uint8", "desc": "Payoff sign identifier" },
    { "name": "settled_amount", "type": "uint64", "desc": "Amount actually reserved or transferred on chain" },
    { "name": "currency_id", "type": "uint64", "desc": "Settlement asset identifier" },
    { "name": "sequence", "type": "uint64", "desc": "Monotonic proof sequence, currently event_id + 1" }
  ]
}
```

## Proof semantics

The following field distinctions are normative for interpreting the receipt:

- `scheduled_time` is the contractual timestamp from the normalized ACTUS schedule.
- `applied_at` is the actual block timestamp at which the kernel applied the event.
- `payoff` is the contractual amount implied by the event.
- `settled_amount` is the amount actually reserved or transferred on chain.
- non-cash executions emit a proof with `settled_amount = 0`.

## Supported ACTUS event identifiers

The current kernel can emit proofs for the following ACTUS event types, subject
to contract-family compatibility:

| Type | Acronym | Description                     |
|:-----|:--------|:--------------------------------|
| `1`  | `IED`   | Initial Exchange Date           |
| `3`  | `PR`    | Principal Redemption            |
| `4`  | `PI`    | Principal Increase              |
| `5`  | `PRF`   | Principal Redemption Fixing     |
| `8`  | `IP`    | Interest Payment                |
| `11` | `RRF`   | Rate Reset Fixing               |
| `12` | `RR`    | Rate Reset                      |
| `18` | `IPCB`  | Interest Calculation Base Reset |
| `19` | `MD`    | Maturity                        |
