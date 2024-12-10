# Summary

[Debt Algorand Standard Asset](./d-asa.md)

---

# Introduction

- [Abstract](./abstract.md)
- [Motivation](./motivation.md)

# Specification

- [Definitions](./definitions.md)
- [Overview](./overview.md)
- [Role-Based Access Control (RBAC)](./rbac.md)
- [Metadata](./metadata.md)
- [Regulations](./regulations.md)
- [Denomination](./denomination.md)
- [Principal (Par)](./principal.md)
- [D-ASA Units](./units.md)
- [Interests](./interests.md)
- [Time Schedule](./time-schedule.md)
  - [Time Events](./time-events.md)
  - [Time Periods](./time-periods.md)
  - [Variable Time Schedule](./variable-time-schedule.md)
- [Day-Count Convention](./day-count-convention.md)
- [Primary Market](./primary-market.md)
- [Payment Agent](./payment-agent.md)
  - [Principal Repayment](./principal-repayment.md)
  - [Early Repayment Options](./early-repayment-options.md)
  - [Coupons Payment](./coupons-payment.md)
- [Transfer Agent](./transfer-agent.md)
- [Secondary Market](./secondary-market.md)

# Interfaces

- [Methods]()
  - [Asset Config](./interface-asset-config.md)
  - [Assign Role](./interface-assign-role.md)
  - [Revoke Role](./interface-revoke-role.md)
  - [Open Account](./interface-open-account.md)
  - [Close Account](./interface-close-account.md)
  - [Set Asset Metadata](./interface-set-asset-metadata.md)
  - [Set Asset Suspension Status](./interface-set-asset-suspension-status.md)
  - [Set Account Suspension Status](./interface-set-account-suspension-status.md)
  - [Set Default Status](./interface-set-default-status.md)
  - [Set Amortizing Rates](./interface-set-amortizing-rates.md)
  - [Set Secondary Time Events](./interface-set-secondary-time-events.md)
  - [Set Early Repayment Time Events](./interface-set-early-repayment-time-events.md)
  - [Primary Distribution](./interface-primary-distribution.md)
  - [Pay Principal](./interface-pay-principal.md)
  - [Pay Coupon](./interface-pay-coupon.md)
  - [Early Repayment](./interface-early-repayment.md)
  - [Asset Transfer](./interface-asset-transfer.md)
  - [Update Total Units](./interface-update-total-units.md)
  - [Update Global Unit Value](./interface-update-global-unit-value.md)
  - [Update Interest Rate](./interface-update-interest-rate.md)
  - [Update Coupon Rates](./interface-update-coupon-rates.md)
  - [Update Time Events](./interface-update-time-events.md)
  - [Update Time Periods](./interface-update-time-periods.md)

- [Getters]()
  - [Get Asset Info](./interface-get-asset-info.md)
  - [Get Asset Metadata](./interface-get-asset-metadata.md)
  - [Get Account Info](./interface-get-account-info.md)
  - [Get Account Units Value](./interface-get-account-units-value.md)
  - [Get Account Units Current Value](./interface-get-account-units-current-value.md)
  - [Get Roles](./interface-get-roles.md)
  - [Get Role Config](./interface-get-role-config.md)
  - [Get Default Status](./interface-get-default-status.md)
  - [Get Time Events](./interface-get-time-events.md)
  - [Get Time Periods](./interface-get-time-periods.md)
  - [Get Coupon Rates](./interface-get-coupon-rates.md)
  - [Get Coupon Amount](./interface-get-coupon-amount.md)
  - [Get Coupon Principal Amount](./interface-get-coupon-principal-amount.md)
  - [Get Coupon Status](./interface-get-coupon-status.md)
  - [Get Amortizing Rates](./interface-get-amortizing-rates.md)
  - [Get Secondary Market Schedule](./interface-get-secondary-market-schedule.md)
  - [Get Early Repayment Schedule](./interface-get-early-repayment-schedule.md)

# Rationale

- [Rationale](./rationale.md)

# Reference Implementation

- [Reference Implementation](./reference-implementation.md)
  - [Zero Coupon Bond]()
  - [Fixed Coupon Bond]()
- [Tests]()

---

[Contributors]()
[License](./LICENSE.md)
