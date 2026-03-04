# Transfer Agent {#transfer-agent}

> Debt instruments can be transferable among investors.

> D-ASA supports both on-chain and off-chain transfer agents.

The Transfer Agent **SHALL** authorize the D-ASA transfers according to the transferability
policy and the secondary market.

The sender and receiver of the D-ASA transfer:

- **MUST** have a valid Holding Addresse, and
- **MUST** be different from each other, and
- **MUST NOT** be suspended from operations.

The sender of the D-ASA transfer **MUST** have sufficient D-ASA *units* to transfer.

The transferred D-ASA *units*:

- **MUST** be non-zero, and
- **MUST** be *fungible* (see [D-ASA Units fungibility](../accounting/units.md#fungibility-fungibility)
section), and
- **MUST** record D-ASA *unit value* and *paid coupons*.

D-ASA *units* **SHALL NOT** be transferred if the sender has pending due coupon
payments.

> The D-ASA transferability policy may involve and integrate KYC/AML processes,
> secondary market restrictions, etc.

If the debt instrument is transferable, the D-ASA **MUST** implement the **OPTIONAL**
`asset_transfer` methods.

The `asset_transfer` method **MAY** be restricted to an authorized Transfer Agent.
