# Overview {#overview}

A *Debt Algorand Standard Application* (D-ASA) is a debt instrument issued as an
Algorand Application, that conforms to this specification, and whose operations
and cash flows are executed on the AVM.

This specification defines the actors of a D-ASA and the interfaces of the Algorand
Application to:

- Arrange and configure the D-ASA (e.g. principal, interest, time events, etc.);
- Manage D-ASA accounts (e.g. opening and closing accounts, etc.);
- Distribute the D-ASA on the primary market (e.g. book building, auctions, etc.);
- Execute D-ASA cash flows (e.g coupon payments, principal repayment, etc.);
- Exchange the D-ASA on secondary markets (if any);
- Query D-ASA information (e.g. due coupons, next coupon due date, etc.).

This specification also provides the interfaces to comply with regulatory requirements,
such as: defining a role-based access control, suspending D-ASA operations completely
or for specific accounts, managing default processes, etc.
