# SDK Overview

The high-level Python API lives directly under `src` and is centered on `DAsa`.

It wraps the generated ARC-56 client in [`src.artifacts.dasa_client`](../../src/artifacts/dasa_client.py)
and keeps the generated ABI structs out of the normal user flow.

```python
from src import (
    DAsa,
    ContractAttributes,
    PricingContext,
    make_pam_zero_coupon_bond,
    normalize_contract_attributes,
)
```

The root package also continues to expose the domain models and the ACTUS normalizer
directly:

- `ContractAttributes`
- `make_pam_zero_coupon_bond(...)`
- `make_pam_fixed_coupon_bond_profile(...)`
- `normalize_contract_attributes(...)`
- `NormalizationResult`
- `NormalizedActusTerms`
- `InitialKernelState`
- `ExecutionScheduleEntry`
- `AccountPosition`
- `ObservedEventRequest`
- `ObservedCashEventRequest`
- `Cycle`

Use `DAsa` for contract interaction, and keep `src.artifacts.dasa_client` as the
explicit low-level escape hatch when needed.
