# Tests {#tests}

The D-ASA project is developed with <a href="https://algorand.co/algokit">AlgoKit</a>.

- Install AlgoKit
- Setup your virtual environment (managed with <a href="https://python-poetry.org/">Poetry</a>)

```shell
algokit bootstrap all
```

- Start your Algorand LocalNet (requires <a href="https://www.docker.com/get-started/">Docker</a>)

```shell
algokit localnet start
```

- Run tests (managed with PyTest)

```shell
algokit project run test
```

or, for verbose results:

```shell
poetry run pytest -s -v tests/<contract_name>/<test_case>.py
```

## Coverage Principles

- Module-level RBAC and Accounting behavior remains in `tests/module_*`.

- Shared CoreFinancial behavior is validated through `tests/shared/*` and runs on:
  - `zero_coupon_bond`
  - `fixed_coupon_bond`
  - `perpetual_bond`

- Product-specific financial behavior remains in contract-specific suites.
