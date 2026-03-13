# D-ASA units {#d-asa-units}

D-ASA units represent pro-rata ownership of the normalized ACTUS contract.

## Total supply

The kernel **MUST** store `total_units` as a `uint64`.

The off-chain normalization process **MUST** derive `total_units` exactly as:

```text
notional_principal / notional_unit_value
```

The division **MUST** be exact. If the principal is not divisible by the chosen
unit value, normalization **MUST** fail.

`notional_unit_value` is an SDK-side normalization input. It is used to derive
`total_units`, but it is not persisted on chain.

## Unit states

A holder account stores two unit balances:

- `reserved_units`: units allocated before `IED`;
- `units`: active units participating in funded ACTUS cashflows.

When `IED` executes, reserved units become activatable and are moved into `units`
the first time the holder position is touched.

## Position accounting

Each holder position **MUST** track:

- The payment address;
- Active and reserved unit balances;
- Suspension state;
- The last settled event cursor;
- The last applied cumulative interest index;
- The last applied cumulative principal index;
- Claimable interest and principal amounts.

The accounting layer does not maintain a mutable on-chain nominal unit value. Transfers
and claims are therefore unit-based and index-based, not value-array-based.

## Lazy settlement

The accounting layer **MUST** settle holder positions lazily against the global
cumulative indices maintained by the kernel.

On settlement:

1. The delta between global and account checkpoints is computed;
1. The delta is multiplied by the holder's active units;
1. The result is moved into `claimable_interest` and `claimable_principal`;
1. The checkpoints and settled cursor are advanced.

This model allows:

- Contract-wide funding of due ACTUS cash events once;
- Account-by-Account realization of the funded cashflows later.
