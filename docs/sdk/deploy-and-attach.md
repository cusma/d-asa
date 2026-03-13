# Deploy and Attach

## Deploy

```python
from src import DAsa

app = DAsa.deploy(
    algorand=algorand,
    arranger=arranger,
    app_name="my-dasa",
)
```

## Deploy and Configure

`deploy_configured(...)` accepts either a precomputed `NormalizationResult` or raw `ContractAttributes` plus the normalization inputs.

```python
app = DAsa.deploy_configured(
    algorand=algorand,
    arranger=arranger,
    normalized=normalized,
    prospectus_url="Issuer term sheet",
)
```

When configuration happens through the high-level API, `DAsa` also stores a `PricingContext` derived from `normalized.terms.notional_unit_value`.

## Attach to an Existing App

```python
app = DAsa.from_app_id(
    algorand=algorand,
    app_id=12345,
)
```

If you already have the generated client:

```python
from src.artifacts.dasa_client import DasaClient

raw_client = DasaClient(algorand=algorand, app_id=12345)
app = DAsa.from_client(raw_client)
```

## Contract View

`app.contract` exposes readonly helpers built from on-chain state:

- `get_state()`
- `get_next_due_event()`
- `get_schedule_entry(event_id)`
- `get_arranger()`
- `get_address_roles(address)`
- `get_role_validity(role, address)`
- `raw_client`
