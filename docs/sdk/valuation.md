# Actualized Positions and Valuation

`HoldingAccount.get_actualized_position()` mirrors the contract's lazy settlement
rules off chain:

- reserved units become active after `IED`
- cumulative interest and principal indices are applied to the holder checkpoints
- the returned position is a preview only; it does not mutate chain state

```python
holder = app.account(investor)
position = holder.get_actualized_position()
```

`get_valuation()` builds on top of that position and adds economic fields:

- `principal_share`
- `claimable_interest`
- `claimable_principal`
- `accrued_interest_not_due`
- `economic_value_total`

```python
valuation = holder.get_valuation()
```

## Trade Quotes

`quote_trade(units=...)` is intended to support secondary-market pricing in the
middle of an accrual period.

The quote always returns:

- the current principal share of the traded units
- accrued interest that is not yet due
- a par-reference clean value
- a par-reference dirty value

If a clean quote is supplied, the SDK derives a market dirty value by adding accrued-not-due
carry.

```python
from decimal import Decimal
from src import TradeQuoteInput

quote = holder.quote_trade(
    25,
    clean_quote=TradeQuoteInput(clean_price_per_100=Decimal("99.25")),
)
```

Important behavior:

- Quotes are rejected when a due ACTUS event is already pending at the requested
timestamp.

- Existing `claimable_interest` and `claimable_principal` remain attached to the
seller account and are reported as retained balances, not transferred unit value.

- `clean_price_per_100` requires a `PricingContext`, because `notional_unit_value`
is SDK metadata and is not stored on chain.
