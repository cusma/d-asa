# Reference Implementation {#reference-implementation}

> ⚠️The reference implementations have not been audited. Do not use this code for
> real products. The author declines all responsibility.

The reference implementation provides the following features:

- RBAC:
  - Arranger: creates, configures and updates the D-ASA
  - Account Manager: opens and closes accounts (proxy a KYC process)
  - Primary Dealer: performs the primary distribution on the primary market
  - Trustee: can call a default
  - Authority: can suspend accounts or the whole asset
  - Interest Oracle: can update the interest rate in case of variable rates

- Denomination:
  - ASA

- Payment Agent:
  - On-chain (ASA)

- Day-count conventions:
  - Actual/Actual (time periods must be in days, i.e., multiples of `86400` seconds)
  - Continuous

- Transfer Agent:
  - On-chain
  - Direct (i.e., from investor to investor)

- Secondary market

- Notarize metadata (e.g. prospectus)

- Updatable program (restricted to the Arranger)

## Deployments {#deployments}

D-ASA examples deployed on TestNet:

| Payoff                                          | App ID | App Spec                                                                                                                  |
|-------------------------------------------------|--------|---------------------------------------------------------------------------------------------------------------------------|
| [Zero Coupon Bond](./ref-zero-coupon-bond.md)   | TBD    | [ARC-32](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/zero_coupon_bond/ZeroCouponBond.arc32.json)   |
| [Fixed Coupon Bond](./ref-fixed-coupon-bond.md) | TBD    | [ARC-32](https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/fixed_coupon_bond/FixedCouponBond.arc32.json) |

1. Download the App Spec JSON file;
1. Navigate to the [Lora App Lab](https://lora.algokit.io/testnet/app-lab);
1. Create the App Interface using the existing App ID and App Spec JSON;
1. Explore the D-ASA interface.
