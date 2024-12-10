# Rationale {#rationale}

This standard has been designed to support different types of debt instruments and
their payoffs, with cash-flows executed both on-chain and off-chain.

The standard fosters modularity, with high degree of flexibility with respect the
integration of external components (Applications), such as KYC, auctions, order-book,
off-chain transfer agents, etc.

The specification makes sure that the trust model and RBAC of D-ASA implementations
can range from trustless versions (e.g. payments triggered automatically if the
conditions are met) to trusted ones (e.g. payments triggered only by authorized
entities).

The implementation of the specified interfaces is left to the use-cases, which may
cherry-pick a subset of methods and getters based on their requirements.
