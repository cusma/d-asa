# Roles

> D-ASA defines custom roles and permissions for the entities involved in the debt
> instrument.

The D-ASA **MUST** define contract roles \\( [CNTRL] \\).

The D-ASA **MUST** identify operational authorities with reserved role identifiers.

The contract roles **MUST** be associated with Algorand Addresses through a role
key of the form:

`[R:||<role key>||#||<role address>]`

Where || denotes concatenation.

The current reference implementation uses the following role set:

|  Key  |  ID  | Role            | Scope                                                                         |
|:-----:|:----:|:----------------|:------------------------------------------------------------------------------|
| `ARR` | `20` | Arranger        | Owns contract creation, configuration, schedule upload, and upgrade authority |
| `OPD` | `25` | Op Daemon       | Optional automation address for payment execution workflows                   |
| `MNG` | `40` | Account Manager | Opens holder accounts                                                         |
| `PYD` | `50` | Primary Dealer  | Allocates units during primary distribution                                   |
| `TRS` | `60` | Trustee         | Sets or clears the contract default-performance flag                          |
| `AUT` | `70` | Authority       | Suspends the contract or individual accounts                                  |
| `MOC` | `80` | Observer        | Applies rate-reset events that depend on observed data                        |

> [!TIP]
> The Arranger with Algorand Address `XYZ` is identified as `R:ARR#XYZ`.

## Role model

The Arranger and Op Daemon are single-address global roles.

The Account Manager, Primary Dealer, Trustee, Authority, and Observer roles are
time-bounded assignments. A role assignment is active only if:

```text
role_validity_start <= current_block_timestamp <= role_validity_end
```

The D-ASA **MUST** reject actions that require an inactive role assignment.

## Responsibilities

### Issuer (Borrower)

> Issuers are individuals, companies, institutions, governments, or other entities
> who borrow capital by issuing a debt.

The Issuer \\( [RPL] \\) is a meta-role in the D-ASA role model, they have no specific
permissions.

### Arranger

> Arrangers are legal entities authorized to arrange debt instruments on behalf
> of the issuers.

The Arranger owns an Algorand Address.

That address **MUST NOT** be the Algorand global zero address.

The Arranger **MUST** be able to:

- create the contract;
- upload normalized ACTUS terms and schedule pages;
- execute `IED`;
- append or apply arranger-controlled observed events;
- rotate the arranger address;
- assign and revoke time-bounded roles;
- update the application.

### Op Daemon

The Op Daemon is an optional execution helper. If configured, the Op Daemon **MAY**
trigger holder cashflow claims in addition to the holder or payment address.

### Account Manager

The Account Manager owns an Algorand Address.

The Account Manager **MUST** be able to open holder accounts. The role does not
control payments or transfers.

> The right to open lender accounts can be granted to different entities, such as
> KYC providers or banks.

### Primary Dealer

The Primary Dealer **MUST** be able to reserve units during primary distribution
before `IED`.

### Trustee

The Trustee role **MUST** control the contract performance \\( [PRF] \\) (see
[Performance](../contract/attributes.md#performance) section for further details).

In the current reference implementation, an active Trustee can set or clear the
contract-level `defaulted` performance flag with `rbac_contract_default`.

This performance flag is distinct from the kernel lifecycle `status`.

### Authority

The Authority owns an Algorand Address.

The Authority **MUST** be able to suspend the contract and individual holder
accounts.

### Observer

> Debt instruments may rely on external data, such as interest rates, covenant breaches,
> etc., provided by trusted oracles.

The Observer \\( [MOC] \\) owns an Algorand Address.

The Observer **MUST** be able to apply due rate-reset events (`RR`, `RRF`) whose
execution depends on observed external values.
