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
  - [Rotate Arranger](./interfaces/rbac/rotate-arranger.md)
  - [Assign Role](./interfaces/rbac/assign-role.md)
  - [Revoke Role](./interfaces/rbac/revoke-role.md)
  - [Governance Asset Suspension](interfaces/rbac/gov-asset-suspension.md)
  - [Get Arranger](./interfaces/rbac/get-arranger.md)
  - [Get Roles](./interfaces/rbac/get-roles.md)
  - [Get Role Config](./interfaces/rbac/get-role-config.md)

- [Account]()
  - [Open](interfaces/account/open.md)
  - [Close](interfaces/account/close.md)
  - [Update Payment Address](./interfaces/account/update-payment-address.md)
  - [Governance Suspension](interfaces/account/gov-suspension.md)
  - [Get Info](interfaces/account/get-info.md)

- [Contract]()
  - [Asset Config](./interfaces/contract/config.md)
  - [Set Metadata](./interfaces/contract/set-metadata.md)
  - [Set Amortizing Rates](./interfaces/contract/set-amortizing-rates.md)
  - [Set Secondary Time Events](./interfaces/contract/set-secondary-time-events.md)
  - [Set Early Repayment Option](./interfaces/contract/set-early-repayment-option.md)
  - [Set Variable Interest Rate](./interfaces/contract/set-variable-interest-rate.md)
  - [Set Default Status](./interfaces/contract/set-default-status.md)
  - [Primary Distribution](./interfaces/contract/primary-distribution.md)
  - [Update Total Units](./interfaces/contract/update-total-units.md)
  - [Update Global Unit Value](./interfaces/contract/update-global-unit-value.md)
  - [Update Interest Rate](./interfaces/contract/update-interest-rate.md)
  - [Update Coupon Rates](./interfaces/contract/update-coupon-rates.md)
  - [Update Time Events](./interfaces/contract/update-time-events.md)
  - [Update Time Periods](./interfaces/contract/update-time-periods.md)
  - [Get Asset Info](./interfaces/contract/get-asset-info.md)
  - [Get Asset Metadata](./interfaces/contract/get-asset-metadata.md)
  - [Get Account Units Value](./interfaces/contract/get-account-units-value.md)
  - [Get Account Units Current Value](./interfaces/contract/get-account-units-current-value.md)
  - [Get Time Events](./interfaces/contract/get-time-events.md)
  - [Get Time Periods](./interfaces/contract/get-time-periods.md)
  - [Get Payment Amount](./interfaces/contract/get-payment-amount.md)
  - [Get Coupon Rates](./interfaces/contract/get-coupon-rates.md)
  - [Get Coupon Status](./interfaces/contract/get-coupon-status.md)
  - [Get Amortizing Rates](./interfaces/contract/get-amortizing-rates.md)
  - [Get Secondary Market Schedule](./interfaces/contract/get-secondary-market-schedule.md)
  - [Get Early Repayment Schedule](./interfaces/contract/get-early-repayment-schedule.md)

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
