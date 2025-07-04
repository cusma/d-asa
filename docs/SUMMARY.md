# Summary

[Debt Algorand Standard Application](./d-asa.md)

---

# Introduction

- [Motivation](./motivation.md)

# Specification

- [Definitions](./definitions.md)
- [Overview](./overview.md)
- [Trust Model]()
  - [Roles](./roles.md)
  - [Role-Based Access Control (RBAC)](./rbac.md)
- [Contract]()
  - [Type](./contract-type.md)
  - [Denomination](./denomination.md)
  - [Principal](./principal.md)
  - [Interests](./interests.md)
    - [Variable Interests](./variable-interests.md)
  - [Time Schedule](./time-schedule.md)
    - [Time Events](./time-events.md)
    - [Time Periods](./time-periods.md)
    - [Variable Time Schedule](./variable-time-schedule.md)
  - [Day-Count Convention](./day-count-convention.md)
  - [Early Repayment Options](./early-repayment-options.md)
  - [Performance](./performance.md)
  - [Metadata](./metadata.md)
- [Ownership]()
  - [D-ASA Units](./units.md)
- [Execution]()
  - [Primary Market](./primary-market.md)
  - [Payment Agent](./payment-agent.md)
    - [Settlement](./settlement.md)
    - [Principal Repayment](./principal-repayment.md)
    - [Early Repayment](./early-repayment.md)
    - [Coupons Payment](./coupons-payment.md)
  - [Transfer Agent](./transfer-agent.md)
  - [Secondary Market](./secondary-market.md)

# Interfaces

- [Methods]()
  - [Asset Config](./methods/interface-asset-config.md)
  - [Assign Role](./methods/interface-assign-role.md)
  - [Revoke Role](./methods/interface-revoke-role.md)
  - [Open Account](./methods/interface-open-account.md)
  - [Close Account](./methods/interface-close-account.md)
  - [Set Asset Metadata](./methods/interface-set-asset-metadata.md)
  - [Set Asset Suspension Status](./methods/interface-set-asset-suspension-status.md)
  - [Set Account Suspension Status](./methods/interface-set-account-suspension-status.md)
  - [Set Default Status](./methods/interface-set-default-status.md)
  - [Set Amortizing Rates](./methods/interface-set-amortizing-rates.md)
  - [Set Secondary Time Events](./methods/interface-set-secondary-time-events.md)
  - [Set Early Repayment Option](./methods/interface-set-early-repayment-option.md)
  - [Set Variable Interest Rate](./methods/interface-set-variable-interest-rate.md)
  - [Primary Distribution](./methods/interface-primary-distribution.md)
  - [Pay Principal](./methods/interface-pay-principal.md)
  - [Pay Coupon](./methods/interface-pay-coupon.md)
  - [Early Repayment](./methods/interface-early-repayment.md)
  - [Asset Transfer](./methods/interface-asset-transfer.md)
  - [Update Total Units](./methods/interface-update-total-units.md)
  - [Update Global Unit Value](./methods/interface-update-global-unit-value.md)
  - [Update Interest Rate](./methods/interface-update-interest-rate.md)
  - [Update Coupon Rates](./methods/interface-update-coupon-rates.md)
  - [Update Time Events](./methods/interface-update-time-events.md)
  - [Update Time Periods](./methods/interface-update-time-periods.md)

- [Getters]()
  - [Get Asset Info](./getters/interface-get-asset-info.md)
  - [Get Asset Metadata](./getters/interface-get-asset-metadata.md)
  - [Get Account Info](./getters/interface-get-account-info.md)
  - [Get Account Units Value](./getters/interface-get-account-units-value.md)
  - [Get Account Units Current Value](./getters/interface-get-account-units-current-value.md)
  - [Get Roles](./getters/interface-get-roles.md)
  - [Get Role Config](./getters/interface-get-role-config.md)
  - [Get Time Events](./getters/interface-get-time-events.md)
  - [Get Time Periods](./getters/interface-get-time-periods.md)
  - [Get Payment Amount](./getters/interface-get-payment-amount.md)
  - [Get Coupon Rates](./getters/interface-get-coupon-rates.md)
  - [Get Coupon Status](./getters/interface-get-coupon-status.md)
  - [Get Amortizing Rates](./getters/interface-get-amortizing-rates.md)
  - [Get Secondary Market Schedule](./getters/interface-get-secondary-market-schedule.md)
  - [Get Early Repayment Schedule](./getters/interface-get-early-repayment-schedule.md)

# Rationale

- [Rationale](./rationale.md)

# Reference Implementation

- [Reference Implementation](./reference-implementation.md)
  - [Zero Coupon Bond](./ref-zero-coupon-bond.md)
  - [Fixed Coupon Bond](./ref-fixed-coupon-bond.md)
  - [Perpetual Bond](./ref-perpetual-bond.md)
- [Tests](./reference-implementation-tests.md)

---

[Contributors](./contributors.md)
[License](./license.md)
