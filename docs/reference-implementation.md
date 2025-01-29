# Reference Implementation {#reference-implementation}

> ⚠️The reference implementations have not been audited. Do not use this code for
> real products. The author declines all responsibility.

> ⚠️The reference implementation does not guarantee compliance with ACTUS reference
> implementation.

The reference implementation provides the following features:

- RBAC:
  - Arranger: creates, configures and updates the D-ASA
  - Account Manager: opens and closes accounts (proxy a KYC process)
  - Primary Dealer: performs the primary distribution on the primary market
  - Trustee: can call a default
  - Authority: can suspend accounts or the whole asset
  - Interest Oracle: can update the interest rate in case of variable rates

- Types:
  - Zero Coupon Bond
  - Fixed Coupon Bond
  - Perpetual Bond

- Denomination:
  - On-chain (ASA)
  - Off-chain

- Payment Agent (Settlement):
  - On-chain (ASA)

- Day-count conventions:
  - Actual/Actual (time periods must be in days, i.e., multiples of `86400` seconds)
  - Continuous

- Transfer Agent:
  - On-chain
  - Direct (i.e., from investor to investor)

- Secondary market

- Notarize metadata (e.g., prospectus, etc.)

- Updatable program (restricted to the Arranger)

## Deployments {#deployments}

D-ASA examples deployed on TestNet:

| Type                                            | App ID                                                                        | App Spec                                                                                                                             |
|-------------------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| [Zero Coupon Bond](./ref-zero-coupon-bond.md)   | <a href="https://lora.algokit.io/testnet/application/733108734">733108734</a> | <a href="https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/zero_coupon_bond/ZeroCouponBond.arc32.json">ARC-32</a>   |
| [Fixed Coupon Bond](./ref-fixed-coupon-bond.md) | <a href="https://lora.algokit.io/testnet/application/733108735">733108735</a> | <a href="https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/fixed_coupon_bond/FixedCouponBond.arc32.json">ARC-32</a> |
| [Perpetual Bond](./ref-perpetual-bond.md)       | <a href="https://lora.algokit.io/testnet/application/733108736">733108736</a> | <a href="https://github.com/cusma/d-asa/blob/main/smart_contracts/artifacts/perpetual_bond/PerpetualBond.arc32.json">ARC-32</a>      |

1. Download the App Spec JSON file;
1. Navigate to the <a href="https://lora.algokit.io/testnet/app-lab">Lora App Lab</a>;
1. Create the App Interface using the existing App ID and App Spec JSON;
1. Explore the D-ASA interface.
