# Summary

[Debt Algorand Standard Application](./COVER.md)

---

# Introduction

- [Motivation](./INTRO.md)
- [Reading Guidelines](./READING-GUIDELINES.md)

# Specification

- [Overview](./specs/overview.md)
- [RBAC Model](./specs/rbac/overview.md)
  - [Roles](./specs/rbac/roles.md)
  - [Role-Based Access Control](./specs/rbac/rbac.md)
- [Contract](./specs/contract/overview.md)
  - [Introduction](./specs/contract/intro.md)
  - [ACTUS Compliance Profile](./specs/contract/actus-compliance-profile.md)
  - [Denomination](./specs/contract/denomination.md)
  - [Day-Count Convention](./specs/contract/day-count-convention.md)
  - [Main Attributes](./specs/contract/attributes.md)
  - [Kernel State and Schedule](./specs/contract/kernel-state-and-schedule.md)
  - [Normalization and Configuration](./specs/contract/normalization-and-configuration.md)
  - [Numeric Precision and Conversions](./specs/contract/numeric-precision.md)
  - [Metadata](./specs/contract/metadata.md)
- [Accounting](./specs/accounting/overview.md)
  - [Account](./specs/accounting/account.md)
  - [Units and Positions](./specs/accounting/units.md)
- [Execution](./specs/execution/overview.md)
  - [Time](./specs/execution/time.md)
  - [Payment Agent](./specs/execution/payment-agent/payment-agent.md)
    - [Settlement](./specs/execution/payment-agent/settlement.md)
  - [Transfer Agent](./specs/execution/transfer-agent/transfer-agent.md)
    - [Primary Distribution](./specs/execution/transfer-agent/primary-market.md)
    - [Secondary Market](./specs/execution/transfer-agent/secondary-market.md)
    - [Delivery-vs-Payment](./specs/execution/transfer-agent/dvp.md)

# Events

- [Events](./events/events.md)

# SDK

- [Overview](./sdk/overview.md)
- [Deploy and Attach](./sdk/deploy-and-attach.md)
- [Role Wrappers](./sdk/roles.md)
- [Actualized Positions and Valuation](./sdk/valuation.md)
- [OTC DvP Builder](./sdk/dvp.md)

# Interfaces

- [Interfaces](./interfaces/overview.md)
  - [ABI Types](./interfaces/types.md)
  - [RBAC Interface](./interfaces/rbac/overview.md)
  - [Accounting Interface](./interfaces/account/overview.md)
  - [ACTUS Kernel Interface](./interfaces/contract/overview.md)
  - [Payment Agent Interface](./interfaces/payment-agent/overview.md)
  - [Transfer Agent Interface](./interfaces/transfer-agent/overview.md)

# Reference Implementation

- [Reference Implementation](./implementation/reference-implementation.md)
  - [Architecture](./implementation/architecture.md)
- [Tests](./implementation/tests.md)
- [DeepWiki (Experimental)](./implementation/deepwiki.md)

---

[Contribution Guidelines](./CONTRIBUTIONS.md)
[License](./LICENSE.md)
