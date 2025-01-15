# Debt Algorand Standard Application {#debt-algorand-standard-application}

![Smart Financial Contract](./images/cover.jpg "Smart Financial Contract")

> A standard for debt instruments tokenization on Algorand

The *Debt Algorand Standard Application* (D-ASA) is a standard for tokenizing *debt
instruments* on the Algorand Virtual Machine.

It provides the interfaces for arranging the asset, configuring its role-based access
control, issuing and distributing it on the primary market, executing cash flows,
exchanging it on the secondary market, and querying information about the debt instrument.

The D-ASA standard conforms, at the best effort[^1], to the *Algorithmic Contract
Types Unified Standards* (<a href="https://www.actusfrf.org/">ACTUS</a>).

The specification allows the tokenization of various debt instruments, such as bonds,
loans, commercial papers, mortgages, etc. A [reference implementation](./reference-implementation.md)
of some fixed income contract examples is provided[^2].

This document is a *technical specification*, it is not to be intended as a legal
or a financial document.

## Contributing {#contributing}

The D-ASA is free and open source. The source code is released on the official
<a href="https://github.com/cusma/d-asa">GitHub repository</a>. External contributions
are welcome, the project relies on the community to improve and expand. Issues and
features requests can be submitted on the <a href="https://github.com/cusma/d-asa/issues">GitHub
issues page</a>. If you would like to contribute, please consider submitting a
<a href="https://github.com/cusma/d-asa/pulls">pull request</a>.

## License {#license}

The D-ASA source and documentation are released under the [AGPL-3.0 license](./license.md).

---

[^1]: ACTUS presents some limitations with respect to blockchain-based implementations.

[^2]: At the current stage, the D-ASA reference implementation does not guarantee
compliance with ACTUS reference implementation.
