# Roles {#roles}

> D-ASA defines custom roles and permissions for the entities involved in the debt
> instrument.

The D-ASA **MUST** define *contract roles* \\([CNTRL]\\).

The *contract roles* **MUST** be identified with a *role ID* (`uint8`).

The *contract roles* **MUST** be associated with Algorand Addresses through a *role
key* of the form:

`[R||<role ID>||#||<role address>]`

Where `||` denotes concatenation.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA role ID `42` associated with the Algorand Address `XYZ`. The
> corresponding role key is `42#XYZ`.

## Issuer (Borrower) {#issuer-(borrower)}

> Issuers are individuals, companies, institutions, governments, or other entities
> who borrow capital by issuing a debt.

An Issuer \\([CRID]\\) is an entity that owes a debt issued as D-ASA.

The Issuer role **MUST** be identified with the reserved ID `1` \\([RPL]\\).

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

Investors \\([CPID]\\) own D-ASA accounts, characterized by a pair of Algorand Addresses:

- *Holding Address*: address that owns D-ASA units with the right to future payments;
- *Payment Address*: address that receives D-ASA payments.

The Payment Address **MAY** be different from the Holding Address.

> D-ASA units can be in custody with a third party or temporarily deposited on an
> order book (Holding Address). At the same time, payments are always executed towards
> the investor (on the Payment Address).

> The right to open and close investor accounts can be granted to different entities,
> such as KYC providers or banks.

The Investor role **MUST** be identified with the reserved ID `30`.

> Debt instruments may have an order of repayment in the event of a sale or default
> of the issuer, based on investors' seniority.

> Investors with the same seniority are treated equally.

The Investors **MAY** have different **seniority** \\([SEN]\\).

### Open Account

The D-ASA accounts **SHALL** be opened using the `open_account` method.

The D-ASA accounts **MUST NOT** be opened if the D-ASA is suspended (see [Suspension](./rbac.md#suspension)
section).

The D-ASA accounts **MUST NOT** be opened if the D-ASA is in default (see [Default](./performance.md#default-default)
section).

### Close Account

The D-ASA accounts **MAY** be closed using the `close_account` method.

The D-ASA accounts **MUST NOT** be closed if the D-ASA is in default (see [Default](./performance.md#default-default)
section).

## Oracles

> Debt instruments may rely on external data, such as interest rates, etc., provided
> by trusted oracles.

An Oracle \\([MOC]\\) is an external entity that provides trusted data to the D-ASA.

A D-ASA **MAY** have multiple oracles.

The Oracle roles **MUST** be identified with the reserved IDs between `80 - 100`.
