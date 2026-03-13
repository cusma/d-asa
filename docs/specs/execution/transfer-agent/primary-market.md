# Primary Market {#primary-market}

> Debt instruments can be distributed on the primary market in different ways, such
> as book building, auctions, etc.

The primary market allocates units before the contract becomes active.

## Allocation phase

`primary_distribution` **MUST** reserve units for an existing holder account while
the contract is in `STATUS_PENDING_IED`.

The method **MUST** reject allocations that:

- Occur before configuration is complete;
- Occur after `IED`;
- Exceed the remaining unallocated supply;
- Target a suspended or missing holder account;
- Request zero units.

Only an active Primary Dealer **MUST** be able to call `primary_distribution`.

## Completion requirement

`contract_execute_ied` **MUST** fail unless:

```text
reserved_units_total == total_units
```

This rule makes full issuance an explicit precondition of activation in the current
reference implementation.

## Activation

Primary distribution reserves units only. Reserved units do not accrue funded ACTUS
cashflows until `IED` executes and the holder position is activated.

## Proxies

The Primary Dealer role **MAY** be delegated to a proxy Application implementing
a primary market.

> [!TIP]
> The primary market is performed as an auction on a dedicated Algorand Application.
> The implementation requires the `primary_distribution` method to be called exclusively
> by the primary market Application, which defines the auction’s outcome.

> [!TIP]
> The primary market is performed as a book building by an authorized Book-builder
> Address. The implementation requires the `primary_distribution` method to be called
> exclusively by the authorized Book-builder.
