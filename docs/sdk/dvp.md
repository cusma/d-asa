# OTC DvP Builder

`HoldingAccount.build_otc_dvp(...)` builds an atomic delivery-vs-payment group for OTC secondary trades.

The builder is intentionally non-custodial:

- it creates the payment leg
- it creates the D-ASA transfer leg
- it returns the composed group for inspection, signing, simulation, or sending

## Algo Settlement

```python
draft = app.account(seller).build_otc_dvp(
    buyer=buyer,
    units=10,
    payment_amount=150_000,
)

result = draft.send()
```

## ASA Settlement

```python
draft = app.account(seller).build_otc_dvp(
    buyer=buyer,
    units=10,
    payment_amount=15_000,
    payment_asset_id=settlement_asa_id,
)
```

## Guardrails

The builder validates:

- `units > 0`
- `payment_amount > 0`
- seller and buyer are different
- the seller signer matches the transfer sender holding address
- optional quote tolerance, when provided

You can combine it with `quote_trade(...)` inputs to fail fast when the negotiated payment amount drifts too far from the SDK's accrual-aware reference.
