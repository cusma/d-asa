# Account (Investor)

> Investors are lenders providing capital to borrowers with the expectation of a
> financial return, defined by debt instruments.

Investors \\( [CPID] \\) own D-ASA accounts, characterized by a pair of Algorand
Addresses:

- *Holding Address*: address that owns D-ASA units with the right to future payments;
- *Payment Address*: address that receives D-ASA payments.

The Payment Address **MAY** be different from the Holding Address.

The Account is uniquely identified by the account key of the form:

`[A#||<role address>]`

Where || denotes concatenation.

> D-ASA units can be in custody with a third party or temporarily deposited on an
> order book (Holding Address). At the same time, payments are always executed
> towards the investor (on the Payment Address).

## Seniority

> Debt instruments may have an order of repayment in the event of a sale or default
> of the issuer, based on investors’ seniority. Investors with the same seniority
> are treated equally.

D-ASA does not enforce investor *seniority* \\( [SEN] \\).
