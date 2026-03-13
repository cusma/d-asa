[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/cusma/d-asa)

# Debt Algorand Standard Application (D-ASA)

Documentation: https://cusma.github.io/d-asa/

The reference implementation follows the execution chain:

```text
ACTUS contract -> AVM normalization -> AVM execution
```

The canonical ABI artifact is:

- `smart_contracts/artifacts/d_asa/DASA.arc56.json`

## Local Setup and Tests

The D-ASA project is developed with [AlgoKit](https://algorand.co/algokit).

- Install AlgoKit
- Set up your virtual environment (managed with [Poetry](https://python-poetry.org/))

```shell
algokit bootstrap all
```

- Start your Algorand LocalNet (requires [Docker](https://www.docker.com/get-started/))

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

## How to contribute

Refer to D-ASA documentation!
