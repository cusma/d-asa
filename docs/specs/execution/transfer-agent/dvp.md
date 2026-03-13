# Delivery-vs-Payment (DvP)

> Delivery-vs-Payment (DvP) can be used to exchange D-ASA units both on the primary
> market (placement) and secondary market (e.g., OTC trades).

The D-ASA framework supports the execution of composable DvP transactions.

The D-ASA DvP transactions are native Algorand Group transactions.

The Algorand Group transactions ensure **atomicity**, they are executed on an "all-or-nothing"
basis, meaning that either all transactions in the group are executed or none of
them are.

Therefore, D-ASA DvP ensures **no counterparty risk**, as the transfer of D-ASA
nits and the corresponding payment occur simultaneously. If either the transfer
or the payment fails, the entire transaction group is rejected, preventing any party
from being left in a vulnerable position.

The simplest DvP consists of:

- A *delivery-leg*, executed by the D-ASA Transfer Agent;
- A *payment-leg*, executed as a general Algorand transaction (usually an ASA transfer).

The **payment** is not restricted to specific assets (e.g., not restricted to the
denomination or settlement assets).

The amounts of the DvP are negotiated between the two parties.
