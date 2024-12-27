# Rationale {#rationale}

This standard has been designed to support different types of debt instruments and
their payoffs, with cash-flows executed both on-chain and off-chain.

The standard fosters modularity, with high degree of flexibility with respect to
the integration of external components (Applications), such as KYC, auctions, order-books,
off-chain transfer agents, etc.

The specification makes sure that the trust model and RBAC of D-ASA implementations
can range from trustless versions (e.g., payments triggered automatically if the
conditions are met, default called automatically on payment failure) to trusted
ones (e.g., payments triggered only by authorized entities, default called manually
by a trustee).

The implementation of the specified interfaces is left to the use-cases, which may
cherry-pick a subset of methods and getters based on their requirements.
