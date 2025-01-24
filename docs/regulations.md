# Regulations {#regulations}

> Debt instruments are regulated under different legal frameworks and their jurisdictions.

> The D-ASA ensures efficient execution of the debt instrument in the "best case
> scenarios", where it offers the highest improvements in cost and time efficiency
> if compared to the traditional, manual, and labor-intensive contracts.

> The D-ASA provides methods to comply with regulatory obligations, allowing the
> management of the "worst case scenarios", in which the intervention of the authority
> or the regulator is necessary.

## Suspension {#suspension}

> Debt instruments can be temporarily suspended due to regulations or operational
> reasons.

### Asset Suspension

The D-ASA **MAY** suspend all:

- Payments;
- D-ASA units transfers.

The asset *suspension* status **MUST** be set with the `set_asset_suspension_status`
method.

### Account Suspension

The D-ASA **MAY** suspend account:

- Payments (skipped on due dates);
- D-ASA units transfers (from and to).

The account *suspension* status **MUST** be set with the `set_account_suspension_status`
method.
