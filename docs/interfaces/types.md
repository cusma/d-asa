# ABI Types

This section documents the canonical ARC-4 structs exposed by the D-ASA ABI.

The types below refer to the on-chain ABI structs in `smart_contracts/abi_types.py`,
not to the richer SDK-side normalization models in `src/models.py`.

## `RoleValidity`

Time-bounded role assignment.

| Field                 | Type     | Meaning                        |
|:----------------------|:---------|:-------------------------------|
| `role_validity_start` | `uint64` | Inclusive activation timestamp |
| `role_validity_end`   | `uint64` | Inclusive expiration timestamp |

## `Prospectus`

Informational contract metadata uploaded with `contract_config`.

| Field  | Type       | Meaning                      |
|:-------|:-----------|:-----------------------------|
| `hash` | `byte[32]` | Prospectus digest            |
| `url`  | `string`   | Prospectus location or label |

## `NormalizedActusTerms`

Normalized ACTUS terms required by the AVM kernel.

| Field                          | Type     | Meaning                                      |
|:-------------------------------|:---------|:---------------------------------------------|
| `contract_type`                | `uint8`  | ACTUS contract family id                     |
| `denomination_asset_id`        | `uint64` | Denomination asset id                        |
| `settlement_asset_id`          | `uint64` | Settlement asset id                          |
| `total_units`                  | `uint64` | Total unit supply                            |
| `notional_principal`           | `uint64` | Notional principal in base units             |
| `initial_exchange_amount`      | `uint64` | Initial exchange amount in base units        |
| `initial_exchange_date`        | `uint64` | `IED` timestamp                              |
| `maturity_date`                | `uint64` | `MD` timestamp, or `0` if absent             |
| `day_count_convention`         | `uint8`  | Supported day-count identifier               |
| `rate_reset_spread`            | `uint64` | Fixed-point spread                           |
| `rate_reset_multiplier`        | `uint64` | Fixed-point rate multiplier                  |
| `rate_reset_floor`             | `uint64` | Fixed-point floor                            |
| `rate_reset_cap`               | `uint64` | Fixed-point cap                              |
| `rate_reset_next`              | `uint64` | Prefixed next rate value                     |
| `has_rate_reset_floor`         | `bool`   | Floor flag                                   |
| `has_rate_reset_cap`           | `bool`   | Cap flag                                     |
| `dynamic_principal_redemption` | `bool`   | Dynamic annuity redemption flag              |
| `fixed_point_scale`            | `uint64` | Fixed-point scale, currently `1_000_000_000` |

SDK-only metadata such as `notional_unit_value` and secondary-market dates is not
part of this ABI struct.

## `InitialKernelState`

Pre-`IED` state snapshot uploaded with `contract_config`.

| Field                        | Type     | Meaning                                    |
|:-----------------------------|:---------|:-------------------------------------------|
| `status_date`                | `uint64` | Reference timestamp for the uploaded state |
| `event_cursor`               | `uint64` | Starting global event cursor               |
| `outstanding_principal`      | `uint64` | Outstanding principal in base units        |
| `interest_calculation_base`  | `uint64` | Interest base in base units                |
| `nominal_interest_rate`      | `uint64` | Current fixed-point nominal rate           |
| `accrued_interest`           | `uint64` | Accrued interest in base units             |
| `next_principal_redemption`  | `uint64` | Next redemption target                     |
| `cumulative_interest_index`  | `uint64` | Per-unit fixed-point interest index        |
| `cumulative_principal_index` | `uint64` | Per-unit fixed-point principal index       |

## `ExecutionScheduleEntry`

One normalized ACTUS schedule entry.

| Field                        | Type     | Meaning                            |
|:-----------------------------|:---------|:-----------------------------------|
| `event_id`                   | `uint64` | Global contiguous event identifier |
| `event_type`                 | `uint8`  | ACTUS event id                     |
| `scheduled_time`             | `uint64` | Due timestamp                      |
| `accrual_factor`             | `uint64` | Fixed-point accrual factor         |
| `redemption_accrual_factor`  | `uint64` | Fixed-point redemption factor      |
| `next_nominal_interest_rate` | `uint64` | Fixed-point next rate              |
| `next_principal_redemption`  | `uint64` | Next redemption state value        |
| `next_outstanding_principal` | `uint64` | Next outstanding principal         |
| `flags`                      | `uint64` | Entry flags                        |

## `ExecutionSchedulePage`

Alias for:

```text
ExecutionScheduleEntry[]
```

The current kernel accepts at most `16` entries per page.

## `ObservedEventRequest`

Observed non-cash event payload used by `apply_non_cash_event`.

| Field                        | Type     | Meaning                          |
|:-----------------------------|:---------|:---------------------------------|
| `event_id`                   | `uint64` | Expected event id when appending |
| `event_type`                 | `uint8`  | ACTUS event id                   |
| `scheduled_time`             | `uint64` | Event timestamp                  |
| `accrual_factor`             | `uint64` | Fixed-point accrual factor       |
| `redemption_accrual_factor`  | `uint64` | Fixed-point redemption factor    |
| `observed_rate`              | `uint64` | Observed fixed-point rate input  |
| `next_nominal_interest_rate` | `uint64` | Fixed-point next rate            |
| `next_principal_redemption`  | `uint64` | Next redemption state value      |
| `next_outstanding_principal` | `uint64` | Next outstanding principal       |
| `flags`                      | `uint64` | Observed-event flags             |

## `ObservedCashEventRequest`

Observed cash event payload used by `append_observed_cash_event`.

| Field                        | Type     | Meaning                          |
|:-----------------------------|:---------|:---------------------------------|
| `event_id`                   | `uint64` | Expected event id when appending |
| `event_type`                 | `uint8`  | ACTUS cash event id              |
| `scheduled_time`             | `uint64` | Event timestamp                  |
| `accrual_factor`             | `uint64` | Fixed-point accrual factor       |
| `redemption_accrual_factor`  | `uint64` | Fixed-point redemption factor    |
| `next_nominal_interest_rate` | `uint64` | Fixed-point next rate            |
| `next_principal_redemption`  | `uint64` | Next redemption state value      |
| `next_outstanding_principal` | `uint64` | Next outstanding principal       |
| `flags`                      | `uint64` | Observed cash-event flags        |

## `KernelState`

Readonly snapshot returned by `contract_get_state`.

| Field                        | Type     | Meaning                          |
|:-----------------------------|:---------|:---------------------------------|
| `contract_type`              | `uint8`  | ACTUS contract family id         |
| `status`                     | `uint64` | Kernel lifecycle status          |
| `total_units`                | `uint64` | Total unit supply                |
| `reserved_units_total`       | `uint64` | Units reserved pre-`IED`         |
| `initial_exchange_amount`    | `uint64` | Initial exchange amount          |
| `event_cursor`               | `uint64` | Current global event cursor      |
| `schedule_entry_count`       | `uint64` | Total uploaded schedule entries  |
| `outstanding_principal`      | `uint64` | Outstanding principal            |
| `interest_calculation_base`  | `uint64` | Current interest base            |
| `nominal_interest_rate`      | `uint64` | Current fixed-point nominal rate |
| `accrued_interest`           | `uint64` | Current accrued interest         |
| `cumulative_interest_index`  | `uint64` | Global per-unit interest index   |
| `cumulative_principal_index` | `uint64` | Global per-unit principal index  |
| `reserved_interest`          | `uint64` | Reserved interest balance        |
| `reserved_principal`         | `uint64` | Reserved principal balance       |

The contract-level `defaulted` performance flag is stored separately in global
state and is not part of `KernelState`.

## `AccountPosition`

Accounting position returned by `account_get_position`.

| Field                  | Type      | Meaning                            |
|:-----------------------|:----------|:-----------------------------------|
| `payment_address`      | `address` | Cashflow destination               |
| `units`                | `uint64`  | Active units                       |
| `reserved_units`       | `uint64`  | Pre-`IED` reserved units           |
| `suspended`            | `bool`    | Account suspension flag            |
| `settled_cursor`       | `uint64`  | Last settled global cursor         |
| `interest_checkpoint`  | `uint64`  | Applied interest index checkpoint  |
| `principal_checkpoint` | `uint64`  | Applied principal index checkpoint |
| `claimable_interest`   | `uint64`  | Claimable interest amount          |
| `claimable_principal`  | `uint64`  | Claimable principal amount         |

## `CashFundingResult`

Result returned by `fund_due_cashflows`.

| Field              | Type     | Meaning                         |
|:-------------------|:---------|:--------------------------------|
| `funded_interest`  | `uint64` | Interest reserved in the call   |
| `funded_principal` | `uint64` | Principal reserved in the call  |
| `total_funded`     | `uint64` | Total reserved amount           |
| `processed_events` | `uint64` | Number of processed cash events |
| `timestamp`        | `uint64` | Execution timestamp             |

## `CashClaimResult`

Result returned by `claim_due_cashflows`.

| Field              | Type     | Meaning                           |
|:-------------------|:---------|:----------------------------------|
| `interest_amount`  | `uint64` | Interest realized or reported     |
| `principal_amount` | `uint64` | Principal realized or reported    |
| `total_amount`     | `uint64` | Total realized or reported amount |
| `timestamp`        | `uint64` | Execution timestamp               |
| `context`          | `byte[]` | Opaque caller-supplied context    |
