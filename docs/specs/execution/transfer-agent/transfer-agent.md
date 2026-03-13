# Transfer Agent {#transfer-agent}

> Debt instruments can be transferable among investors.

> D-ASA supports both on-chain and off-chain transfer agents.

The Transfer Agent executes primary and secondary movement of D-ASA units.

## Secondary transfers

`transfer` **MUST** move active units only after:

- The contract is active;
- The transfer window is open, if a window was configured;
- Both counterparties are valid, distinct, and unsuspended accounts;
- Both counterparties are settled to the current global indices;
- There is no due ACTUS event pending at the global cursor.

The sender of the D-ASA transfer **MUST** have enough D-ASA *units* to transfer.

The method **MUST** return the number of units transferred.

Transfers are unit-based. The current kernel does not persist a mutable per-unit
nominal value or per-unit coupon status.

## Caller model

> The D-ASA transferability policy may involve and integrate KYC/AML processes,
> pre-authorizations, secondary market restrictions, etc.

The current reference implementation requires the holder to call `transfer` directly.

The method **MUST** reject calls from any other address. Transfers are therefore
direct holder actions, not transfer-agent proxy calls.
