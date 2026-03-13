# Reference Implementation {#reference-implementation}

> ⚠️The reference implementation has not been audited. Do not use this code for
> real products. The author declines all responsibility.

The reference implementation exposes one canonical on-chain contract, `DASA`, and
composes it from five modules:

- `RbacModule`
- `ActusKernelModule`
- `AccountingModule`
- `PaymentAgent`
- `TransferAgent`

The implementation executes normalized ACTUS schedules on the AVM and currently
supports the kernel contract families `PAM`, `ANN`, `NAM`, `LAM`, `LAX`, and `CLM`.

## Delivered artifacts

The canonical artifacts are:

- `src/artifacts/DASA.arc56.json`
- `src/artifacts/dasa_client.py`
- `src/artifacts/dasa_avm_client.py`

The deployment helpers in `smart_contracts/d_asa/deploy_config.py` provide code-accurate
demo normalization flows for:

- a PAM fixed coupon bond profile;
- a PAM zero coupon bond profile.

Those demos are examples of normalized inputs to the shared kernel, not separate
contract classes with different public ABIs.
