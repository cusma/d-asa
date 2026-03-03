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
  - [Set Default Status](./interfaces/rbac/set-default-status.md)
  - [Get Arranger](./interfaces/rbac/get-arranger.md)
  - [Get Roles](./interfaces/rbac/get-roles.md)
  - [Get Role Config](./interfaces/rbac/get-role-config.md)

- [Account]()
  - [Open](interfaces/account/open.md)
  - [Close](interfaces/account/close.md)
  - [Update Payment Address](./interfaces/account/update-payment-address.md)
  - [Governance Suspension](interfaces/account/gov-suspension.md)
  - [Get Info](interfaces/account/get-info.md)

- [Asset]()
  - [Asset Config](asset/config.md)
  - [Set Metadata](asset/set-metadata.md)
  - [Set Amortizing Rates](asset/set-amortizing-rates.md)
  - [Set Secondary Time Events](asset/set-secondary-time-events.md)
  - [Set Early Repayment Option](asset/set-early-repayment-option.md)
  - [Set Variable Interest Rate](asset/set-variable-interest-rate.md)
  - [Primary Distribution](asset/primary-distribution.md)
  - [Update Total Units](asset/update-total-units.md)
  - [Update Global Unit Value](asset/update-global-unit-value.md)
  - [Update Interest Rate](asset/update-interest-rate.md)
  - [Update Coupon Rates](asset/update-coupon-rates.md)
  - [Update Time Events](asset/update-time-events.md)
  - [Update Time Periods](asset/update-time-periods.md)
  - [Get Asset Info](asset/get-asset-info.md)
  - [Get Asset Metadata](asset/get-asset-metadata.md)
  - [Get Account Units Value](asset/get-account-units-value.md)
  - [Get Account Units Current Value](asset/get-account-units-current-value.md)
  - [Get Time Events](asset/get-time-events.md)
  - [Get Time Periods](asset/get-time-periods.md)
  - [Get Payment Amount](asset/get-payment-amount.md)
  - [Get Coupon Rates](asset/get-coupon-rates.md)
  - [Get Coupon Status](asset/get-coupon-status.md)
  - [Get Amortizing Rates](asset/get-amortizing-rates.md)
  - [Get Secondary Market Schedule](asset/get-secondary-market-schedule.md)
  - [Get Early Repayment Schedule](asset/get-early-repayment-schedule.md)

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
