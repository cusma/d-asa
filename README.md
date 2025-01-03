# Debt Algorand Standard Application (D-ASA)

Documentation: TBD

## Deployments {#deployments}

D-ASA examples deployed on TestNet:

| Payoff                                          | App ID | App Spec                                                                                                                  |
|-------------------------------------------------|--------|---------------------------------------------------------------------------------------------------------------------------|
| [Zero Coupon Bond](./ref-zero-coupon-bond.md)   | TBD    | [ARC-32](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/zero_coupon_bond/ZeroCouponBond.arc32.json)   |
| [Fixed Coupon Bond](./ref-fixed-coupon-bond.md) | TBD    | [ARC-32](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/fixed_coupon_bond/FixedCouponBond.arc32.json) |
| [Perpetual Bond](./ref-perpetual-bond.md)       | TBD    | [ARC-32](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/perpetual_bond/PerpetualBond.arc32.json)      |

1. Download the App Spec JSON file;
1. Navigate to the [Lora App Lab](https://lora.algokit.io/testnet/app-lab);
1. Create the App Interface using the existing App ID and App Spec JSON;
1. Explore the D-ASA interface.

## Local Setup and Tests

The D-ASA project is developed with [AlgoKit](https://algorand.co/algokit).

- Install AlgoKit
- Setup your virtual environment (managed with [Poetry](https://python-poetry.org/))

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

Refer to D-ASA documentation.
