# Role-Based Access Control {#role-based-access-control}

> D-ASA can define a custom role-based access control to comply with administrative
> and regulatory requirements.

A D-ASA *role* **MAY** be assigned using the **OPTIONAL** `assign_role` method.

A D-ASA *role* **MAY** be revoked using the **OPTIONAL** `revoke_role` method.

## Suspension

> Debt instruments are regulated under different legal frameworks and their jurisdictions.

> The D-ASA ensures efficient execution of the debt instrument in the "best case
> scenarios", where it offers the highest improvements in cost and time efficiency
> if compared to the traditional, manual, and labor-intensive contracts.

> The D-ASA provides methods to comply with regulatory obligations, allowing the
> management of the "worst case scenarios", in which the intervention of the authority
> or the regulator is necessary.

> Debt instruments can be temporarily suspended due to regulations or operational
> reasons.

The D-ASA suspension authority **MUST** be restricted to specific *contract roles*.

### Asset Suspension

The D-ASA **MAY** suspend all:

- Payments;
- D-ASA units transfers.

The asset *suspension* status **MUST** be set with the `set_asset_suspension_status`
method.

### Account Suspension

The D-ASA **MAY** suspend an account:

- Payments (skipped on due dates);
- D-ASA units transfers (from and to).

The account *suspension* status **MUST** be set with the `set_account_suspension_status`
method.
