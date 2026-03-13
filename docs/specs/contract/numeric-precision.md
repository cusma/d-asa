# Numeric Precision and Conversions

All values uploaded to the kernel **MUST** fit into AVM `uint64` values.

## Amounts

Display amounts are normalized into ASA base units:

```text
base_units = int(display_amount * 10^decimals)
```

The conversion truncates toward zero because normalization converts the scaled decimal
value to an integer directly.

## Rates

Rates are normalized into fixed-point integers with:

```text
fixed_point_rate = int(rate * 1_000_000_000)
```

The D-ASA fixed-point scale is:

```text
FIXED_POINT_SCALE = 1_000_000_000
```

The kernel then uses wide multiplication and division to apply those rates safely
on chain.

## Units

The normalization process **MUST** derive the total unit supply from:

```text
total_units = notional_principal / notional_unit_value
```

This division **MUST** be exact.

## Initial exchange amount

The initial exchange amount is normalized as:

```text
initial_exchange_amount = notional - discount
initial_exchange_amount = notional + premium
```

where:

- a positive `premium_discount_at_ied` is treated as a discount;
- a negative `premium_discount_at_ied` is treated as a premium.

Normalization **MUST** fail if the result becomes negative or exceeds `uint64`.

## Overflow constraints

Every normalization step **MUST** reject:

- negative amounts that would require signed integers on chain;
- values larger than `2^64 - 1`;
- scaled amounts or rates that overflow after multiplication by their scale.

## Example

For a denomination asset with `2` decimals:

- `10_000` display units normalize to `1_000_000` base units;
- `100` display units normalize to `10_000` base units;
- `0.02` normalizes to `20_000_000` fixed-point units;
- `1_000_000 / 10_000 = 100` total units.

## Cumulative indices

The accounting layer uses fixed-point cumulative indices for contract-wide cashflow
funding:

- Contract-wide amount -> Per-unit index delta;
- Per-unit index delta -> Claim at settlement time.

This design preserves precision at contract level while keeping holder settlement
lazy and deterministic.
