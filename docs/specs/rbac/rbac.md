# Role-Based Access Control {#role-based-access-control}

The D-ASA role model **MUST** gate every privileged ABI method.

## Role administration

The Arranger **MUST** control role administration through:

- `rbac_assign_role`
- `rbac_revoke_role`
- `rbac_get_role_validity`
- `rbac_get_address_roles`

Role assignments **MUST** be validated against their stored time window at execution
time. A role that exists but is outside its validity interval **MUST** be treated
as inactive.

## Arrangement

The Arranger **MUST** retain the authority to:

- rotate the arranger address with `rbac_rotate_arranger`;
- set the optional operation daemon with `rbac_set_op_daemon`;
- update the application with `contract_update`.

## Suspension

> Debt instruments are regulated under different legal frameworks and their jurisdictions.

> The D-ASA ensures efficient execution of the debt instrument in the “best case
> scenarios”, where it offers the highest improvements in cost and time efficiency
> if compared to the traditional, manual, and labor-intensive contracts.

> The D-ASA provides methods to comply with regulatory obligations, allowing the
> management of the “worst case scenarios”, in which the intervention of the authority
> or the regulator is necessary.

> Debt instruments can be temporarily suspended due to regulations or operational
> reasons.

The D-ASA suspension authority **MUST** be restricted to specific contract roles.

### Asset suspension

`rbac_contract_suspension` **MUST** suspend or resume asset-wide operations.

When the asset is suspended, the implementation **MUST** reject:

- primary distribution;
- funding and claiming of due cashflows;
- holder payment-address updates;
- transfers;
- any other method explicitly guarded by the suspension flag.

### Account suspension

`account_suspension` **MUST** suspend or resume a specific holder account.

When an account is suspended, the implementation **MUST** reject:

- unit allocations to that account during primary distribution;
- transfers from or to that account;
- on-chain cashflow execution to that account while the suspension remains in force.

## Trustee-controlled default

`rbac_contract_default` **MUST** be restricted to the Trustee role.

In the current reference implementation, this method sets or clears the contract-level
`defaulted` performance flag in RBAC global state. It does not change the kernel
lifecycle `status`.

## Observer-controlled events

The Observer role **MUST** authorize due `RR` and `RRF` event application through
`apply_non_cash_event`.

All other non-cash events remain arranger-controlled unless a future profile explicitly
states otherwise.
