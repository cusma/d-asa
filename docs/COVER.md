# Debt Algorand Standard Application {#debt-algorand-standard-application}

```toml
{{#include ../pyproject.toml:3:3}}
```

![Smart Financial Contract](./images/cover.jpg "Smart Financial Contract")

> A standard for debt instruments tokenization on Algorand

The *Debt Algorand Standard Application* (D-ASA) is a standard for tokenizing *debt
instruments* on the Algorand Virtual Machine.

It provides a framework for arranging the contract, configuring its role-based access
control, issuing and distributing it on the primary market, executing cash flows,
exchanging it on the secondary market, and querying information about the debt instrument.

The specification complies with the *Algorithmic Contract Types Unified Standards*
(<a href="https://www.actusfrf.org/">ACTUS</a>) for the definition of the contracts.

**D-ASA is, in essence, a full tokenization framework for ACTUS-compliant debt instruments,
issued and executed on the Algorand Virtual Machine.**

The specification allows the tokenization of various debt instruments, such as bonds,
loans, commercial papers, mortgages, etc.

The [reference implementation](./implementation/reference-implementation.md) of
some fixed income contracts is provided.

This document is a *technical specification*, it is not intended to be a legal or
a financial document.

## Contents

Contents are organized in three hierarchical levels (see the navigation sidebar
on the left):

```text
Part
└── 1. Chapter
    └── 1.1. Section
        └── 1.1.1. Sub-section
```

The navigation sidebar can be folded up to the *Chapter* level by clicking the folding
icon (**>**), next to the level name.

## Contributing {#contributing}

The D-ASA is free and open source.

The source code is released on the official [GitHub repository](https://github.com/cusma/d-asa).

External contributions are welcome, the project relies on the community to improve
and expand.

Issues and feature requests can be submitted on the [GitHub issues page](https://github.com/cusma/d-asa/issues).

If you would like to contribute, please read the [guidelines](./CONTRIBUTIONS.md#guidelines-guidelines)
and consider submitting a [pull request](https://github.com/cusma/d-asa/pulls).

## License {#license}

The D-ASA source and documentation are released under the [AGPL-3.0 license](./LICENSE.md).
