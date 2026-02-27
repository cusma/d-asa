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
