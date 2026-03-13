# Normalization and Configuration

The contract configuration flow **MUST** follow the same sequence as the reference
implementation:

```text
ContractAttributes -> normalize_contract_attributes() -> contract_config() -> contract_schedule() -> primary_distribution() -> contract_execute_ied()
```

## Required steps

1. Define the debt instrument with `ContractAttributes`.

1. Normalize the contract off chain with `normalize_contract_attributes()`.

1. Upload `NormalizedActusTerms`, `InitialKernelState`, and the prospectus with
`contract_config`.

1. Upload the normalized schedule in contiguous pages with `contract_schedule`.

1. Reserve all units with `primary_distribution`.

1. Activate issuance by executing `contract_execute_ied`.

`contract_schedule` **MUST** be called after `contract_config`, and `contract_execute_ied`
**MUST** be called only after the full schedule is uploaded and the full unit supply
is reserved.

## Example

The deployment helpers and tests provide a code-accurate PAM fixed coupon bond example:

```python
attrs = make_pam_fixed_coupon_bond_profile(
    contract_id=1,
    status_date=1_700_000_000,
    initial_exchange_date=1_702_592_000,
    maturity_date=1_858_112_000,
    notional_principal=10_000,
    nominal_interest_rate=0.02,
    interest_payment_cycle=Cycle.parse_cycle("90D"),
    interest_payment_anchor=1_710_368_000,
)

normalized = normalize_contract_attributes(
    attrs,
    denomination_asset_id=12345,
    denomination_asset_decimals=2,
    notional_unit_value=100,
    secondary_market_opening_date=1_702_592_000,
    secondary_market_closure_date=1_858_198_400,
)

pages = normalized.schedule_pages(page_size=16)
```

The normalized result has the following properties:

- `notional_principal = 1_000_000` base units;
- `total_units = 100`;
- `fixed_point_scale = 1_000_000_000`;
- `schedule = [IED] + 20 * [IP] + [MD]`;
- `len(schedule) = 22`;
- `len(pages) = 2`.

The upload sequence is:

```python
client.send.contract_config(...)
client.send.contract_schedule(schedule_page_index=0, is_last_page=False, ...)
client.send.contract_schedule(schedule_page_index=1, is_last_page=True, ...)
client.send.primary_distribution(...)
client.send.contract_execute_ied()
```

## Schedule paging

Schedule paging is part of configuration, not a transport detail. The caller **MUST**
preserve:

- contiguous `schedule_page_index` values;
- contiguous `event_id` values across pages;
- chronological ordering across page boundaries;
- one final page flagged with `is_last_page = true`.

## Secondary-market configuration

`transfer_set_schedule` is separate from kernel configuration. Secondary-market
dates are not part of the on-chain `NormalizedActusTerms` struct in the current
ABI and, if enforced, **MUST** be configured separately at the execution layer.

## Performance state

The contract-level `defaulted` performance flag is not part of normalization or
`InitialKernelState`. If used, it is updated separately at execution time through
`contract_set_default_status`.
