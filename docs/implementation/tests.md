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

The repository also includes a D-ASA showcase walkthrough that prints the
normalized ACTUS schedule beside the real ARC-28 execution proofs and realized
cashflows for PAM fixed coupon and zero coupon bonds:

```shell
poetry run pytest -s -v -m showcase tests/pam/test_pam_lifecycle_showcase.py
```

## Coverage Areas

- `tests/sdk/*` covers the Python-side SDK and normalization layer: contract
  builders, schedules, day-count conventions, registry mappings, models, and
  deploy configuration helpers.

- `tests/mock_module_rbac/*` exercises RBAC behavior in isolation through the
  dedicated mock module artifact.

- `tests/pam/fcb/*` and `tests/pam/zcb/*` run end-to-end PAM lifecycle tests on
  LocalNet for fixed coupon and zero coupon bonds, including schedule upload,
  `IED`, cashflow funding, holder claims, and final contract state.

- `tests/pam/test_pam_lifecycle_showcase.py` is the narrative walkthrough suite
  for new users. It prints the normalized ACTUS schedule beside the emitted
  ARC-28 execution receipts and realized cashflows. It is marked `showcase` and
  excluded from the default `algokit project run test` command.

- Shared fixtures live in `tests/conftest.py`, `tests/pam/conftest.py`, and
  `tests/conftest_helpers.py`; helper decoding and time-warp utilities live in
  `tests/utils.py`.
