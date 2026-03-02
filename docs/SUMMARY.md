# Summary

[Debt Algorand Standard Application](./COVER.md)

---

# Introduction

- [Motivation](./motivation.md)
- [Reading Guidelines](./READING-GUIDELINES.md)

# Specification

- [Overview](./specs/overview.md)
- [Trust Model]()
  - [Roles](./specs/rbac/roles.md)
  - [Role-Based Access Control (RBAC)](./specs/rbac/rbac.md)
- [Contract](specs/contract/intro.md)
  - [Type](./specs/contract/type.md)
  - [Denomination](./specs/contract/denomination.md)
  - [Principal](./specs/contract/principal.md)
  - [Interests](./specs/contract/interests.md)
    - [Variable Interests](./specs/contract/variable-interests.md)
  - [Time Schedule](./specs/contract/time-schedule.md)
    - [Time Events](./specs/contract/time-events.md)
    - [Time Periods](./specs/contract/time-periods.md)
    - [Variable Time Schedule](./specs/contract/variable-time-schedule.md)
  - [Day-Count Convention](./specs/contract/day-count-convention.md)
  - [Early Repayment Options](./specs/contract/early-repayment-options.md)
  - [Performance](./specs/contract/performance.md)
  - [Metadata](./specs/contract/metadata.md)
- [Accounting]()
  - [D-ASA Units](./specs/accounting/units.md)
- [Execution]()
  - [Primary Market](./specs/execution/primary-market.md)
  - [Payment Agent](./specs/execution/payment-agent/payment-agent.md)
    - [Settlement](./specs/execution/payment-agent/settlement.md)
    - [Principal Repayment](./specs/execution/payment-agent/principal-repayment.md)
    - [Early Repayment](./specs/execution/payment-agent/early-repayment.md)
    - [Coupons Payment](./specs/execution/payment-agent/coupons-payment.md)
  - [Transfer Agent](./specs/execution/transfer-agent.md)
  - [Secondary Market](./specs/execution/secondary-market.md)

# Interfaces

- [RBAC]()
  - [Rotate Arranger]()
  - [Assign Role](./interfaces/rbac/assign-role.md)
  - [Revoke Role](./interfaces/rbac/revoke-role.md)
  - [Governance Asset Suspension](interfaces/rbac/gov-asset-suspension.md)
  - [Set Default Status](./interfaces/rbac/set-default-status.md)
  - [Get Arranger]()
  - [Get Roles](./interfaces/rbac/get-roles.md)
  - [Get Address Roles]()
  - [Get Role Config](./interfaces/rbac/get-role-config.md)

- [Account]()
  - [Open](interfaces/account/open.md)
  - [Close](interfaces/account/close.md)
  - [Governance Suspension](interfaces/account/gov-suspension.md)
  - [Get Info](interfaces/account/get-info.md)
  - [Get Account Units Value](./getters/interface-get-account-units-value.md)
  - [Get Account Units Current Value](./getters/interface-get-account-units-current-value.md)

- [Asset]()
  - [Asset Config](./methods/interface-asset-config.md)
  - [Set Asset Metadata](./methods/interface-set-asset-metadata.md)
  - [Set Amortizing Rates](./methods/interface-set-amortizing-rates.md)
  - [Set Secondary Time Events](./methods/interface-set-secondary-time-events.md)
  - [Set Early Repayment Option](./methods/interface-set-early-repayment-option.md)
  - [Set Variable Interest Rate](./methods/interface-set-variable-interest-rate.md)
  - [Primary Distribution](./methods/interface-primary-distribution.md)
  - [Update Total Units](./methods/interface-update-total-units.md)
  - [Update Global Unit Value](./methods/interface-update-global-unit-value.md)
  - [Update Interest Rate](./methods/interface-update-interest-rate.md)
  - [Update Coupon Rates](./methods/interface-update-coupon-rates.md)
  - [Update Time Events](./methods/interface-update-time-events.md)
  - [Update Time Periods](./methods/interface-update-time-periods.md)
  - [Get Asset Info](./getters/interface-get-asset-info.md)
  - [Get Asset Metadata](./getters/interface-get-asset-metadata.md)
  - [Get Time Events](./getters/interface-get-time-events.md)
  - [Get Time Periods](./getters/interface-get-time-periods.md)
  - [Get Payment Amount](./getters/interface-get-payment-amount.md)
  - [Get Coupon Rates](./getters/interface-get-coupon-rates.md)
  - [Get Coupon Status](./getters/interface-get-coupon-status.md)
  - [Get Amortizing Rates](./getters/interface-get-amortizing-rates.md)
  - [Get Secondary Market Schedule](./getters/interface-get-secondary-market-schedule.md)
  - [Get Early Repayment Schedule](./getters/interface-get-early-repayment-schedule.md)

- [Payment Agent]()
  - [Pay Coupon](./interfaces/payment-agent/pay-coupon.md)
  - [Pay Principal](./interfaces/payment-agent/pay-principal.md)
  - [Early Repayment](interfaces/payment-agent/early-repayment.md)

- [Transfer Agent]()
  - [Asset Transfer](./interfaces/transfer-agent/asset-transfer.md)

# Rationale

- [Rationale](./rationale.md)

# Reference Implementation

- [Reference Implementation](./implementation/reference-implementation.md)
  - [Architecture](./implementation/architecture.md)
  - [Zero Coupon Bond](./implementation/ref-zero-coupon-bond.md)
  - [Fixed Coupon Bond](./implementation/ref-fixed-coupon-bond.md)
  - [Perpetual Bond](./implementation/ref-perpetual-bond.md)
- [Tests](./implementation/reference-implementation-tests.md)

---

[Contribution Guidelines](./CONTRIBUTIONS.md)
[License](LICENSE.md)
