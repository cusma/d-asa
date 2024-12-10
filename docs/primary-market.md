# Primary Market {#primary-market}

> Debt instruments can be distributed on the primary market in different ways, such
> as book building, auctions, etc.

The D-ASA units **MUST** be distributed to D-ASA accounts, at most up to *total
units*, using the `primary_distribution` method.

The primary distribution of D-ASA *units* **SHALL** be completed between the *primary
distribution opening* and *closing dates*, according to the primary market.

The `primary_distribution` method **MUST** be called by an authorized primary distribution
entity.

> 📎 **EXAMPLE**
>
> The primary market is performed as an auction on a dedicated Algorand Application.
> The implementation requires the `primary_distribution` method to be called exclusively
> by the primary market Application, which defines the auction’s outcome.

> 📎 **EXAMPLE**
>
> The primary market is performed as a book building by an authorized Book-builder
> Address. The implementation requires the `primary_distribution` method to be called
> exclusively by the authorized Book-builder.
