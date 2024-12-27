# Reference Implementation {#reference-implementation}

The reference implementation provides the following features:

- RBAC:
  - Arranger: creates, configures and updates the D-ASA
  - Account Manager: opens and closes accounts (proxy a KYC process)
  - Primary Dealer: performs the primary distribution on the primary market
  - Trustee: can call a default
  - Authority: can suspend accounts or the whole asset

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

## Payoffs

- [Zero Coupon Bond](./ref-zero-coupon-bond.md)
- [Fixed Coupon Bond](./ref-fixed-coupon-bond.md)
