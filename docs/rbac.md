# Roles {#roles}

> D-ASA defines custom roles and permissions for the entities involved in the debt
> instrument.

Roles **MUST** be identified with a *role ID* (`uint8`).

Roles **MUST** be associated with Algorand Addresses through a *role key* of the
form:

`[R||<role ID>||#||<role address>]`

Where `||` denotes concatenation.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA role ID `42` associated with the Algorand Address `XYZ`. The
> corresponding role key is `42#XYZ`.

## Issuer (Borrower) {#issuer-(borrower)}

> Issuers are individuals, companies, institutions, governments, or other entities
> who borrow capital by issuing a debt.

An Issuer is an entity that owes a debt issued as D-ASA.

The Issuer role **MUST** be identified with the reserved ID `10`.

## Arranger {#arranger}

> Arrangers are legal entities authorized to arrange debt instruments on behalf
> of the issuers.

The Arranger owns an Algorand Address.

The Arranger role **MUST** be identified with the reserved ID `20`.

The Arranger **SHALL** configure the D-ASA using the `asset_config` method.

The Arranger **MAY** configure the D-ASA *role-based access control* with the **OPTIONAL**
`assign_role` and `revoke_role` methods.

## Investor (Lender) {#investor-(lender)}

> Investors are lenders providing capital to borrowers with the expectation of a
> financial return, defined by debt instruments.

Investors own D-ASA accounts, characterized by a pair of Algorand Addresses:

- *Holding Address*: address that owns D-ASA units with the right to future payments;
- *Payment Address*: address that receives D-ASA payments.

The Payment Address **MAY** be different from the Holding Address.

> D-ASA units can be in custody with a third party or temporarily deposited on an
> order book (Holding Address). At the same time payments are always executed towards
> the lender (on the Payment Address).

> The right to open and close investor accounts can be granted to different entities,
> such as KYC providers or banks.

The Investor role **MUST** be identified with the reserved ID `30`.

## Open Account

The D-ASA accounts **SHALL** be opened using the `open_account` method.

The D-ASA accounts **MUST NOT** be opened if the D-ASA is suspended (see [Suspension](./regulations.md#suspension-suspension)
section).

The D-ASA accounts **MUST NOT** be opened if the D-ASA is in default (see [Default](./regulations.md#default-default)
section).

## Close Account

The D-ASA accounts **MAY** be closed using the `close_account` method.

The D-ASA accounts **MUST NOT** be closed if the D-ASA is in default (see [Default](./regulations.md#default-default)
section).

## Role-Based Access Control {#role-based-access-control}

> D-ASA can define a custom role-based access control to comply with administrative
> and regulatory requirements.

A D-ASA *role* **MAY** be assigned using the **OPTIONAL** `assign_role` method.

A D-ASA *role* **MAY** be revoked using the **OPTIONAL** `revoke_role` method.
