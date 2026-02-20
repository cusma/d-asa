# Debt Algorand Standard Application (D-ASA)

Documentation: https://cusma.github.io/d-asa/

## Deployments

D-ASA examples deployed on TestNet:

| Type              | App ID                                                             | App Spec                                                                                                                  |
|-------------------|--------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Zero Coupon Bond  | [733151482](https://lora.algokit.io/testnet/application/733151482) | [ARC-56](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/zero_coupon_bond/ZeroCouponBond.arc56.json)   |
| Fixed Coupon Bond | [733151497](https://lora.algokit.io/testnet/application/733151497) | [ARC-56](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/fixed_coupon_bond/FixedCouponBond.arc56.json) |
| Perpetual Bond    | [733151498](https://lora.algokit.io/testnet/application/733151498) | [ARC-56](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/perpetual_bond/PerpetualBond.arc56.json)      |

1. Download the App Spec JSON file;
1. Navigate to the [Lora App Lab](https://lora.algokit.io/testnet/app-lab);
1. Create the App Interface using the existing App ID and App Spec JSON;
1. Explore the D-ASA interface.

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
