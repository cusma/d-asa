# Contribution {#contribution}

The D-ASA is free and open source.

The source code is released on the official
<a href="https://github.com/cusma/d-asa">GitHub repository</a>.

External contributions are welcome, the project relies on the community to improve
and expand. Issues and features requests can be submitted on the <a href="https://github.com/cusma/d-asa/issues">GitHub
issues page</a>.

If you would like to contribute, please read the [guidelines](./contributors.md#guidelines-guidelines)
and consider submitting a <a href="https://github.com/cusma/d-asa/pulls">pull request</a>.

## Contributors {#contributors}

- Cosimo Bassi ([@cusma](https://github.com/cusma/))
- Altynbek Orumbayev ([@aorumbayev](https://github.com/aorumbayev))

## Guidelines {#guidelines}

By clicking on the _“Suggest an edit”_ icon in the top-right corner, while reading
this book, you will be redirected to the relevant source code file to be referenced
in an issue or edited in a pull request.

### Source Code

The D-ASA Specifications book is built with [mdBook](https://rust-lang.github.io/mdBook/index.html).

The source code is structured as follows:

```text
.algokit/                -> AlgoKit configurations
.github/                 -> GitHub actions and CI/CD workflows
docs/                    -> mdBook source code
└── .include/            -> ABI Interfaces, templates, etc.
└── images/              -> Image files
└── getters/             -> D-ASA Getters interfaces
└── methods/             -> D-ASA Methods interfaces
└── SUMMARY.md, ...      -> mdBook SUMMARY.md, cover, chapters, sections, etc.
smart_contracts/         -> D-ASA Smart Contracts
└── artifacts/           -> AlgoKit auto-generated artifacts
└── base_d_asa/          -> Base D-ASA Contract from which others inherit
└── contract_a/          -> Contract Type A
└── contract_b/          -> Contract Type B
└── contract_.../        -> Contract Type ...
    └── config.py        -> Contract configuration
    └── contract.py      -> Contract implementation
    └── deploy_config.py -> Contract deployment configuration
tests/                   -> Tests of D-ASA Smart Contracts
└── base_d_asa/          -> Tests of Base D-ASA
└── contract_a/          -> Tests of Contract Type A
|   └── conftest.py      -> Contract Type A test fixtures
|   └── test_method_1.py -> Tests of Contract Type A Method 1
|   └── test_method_2.py -> Tests of Contract Type A Method 2
|   └── test_method_...  -> Tests of Contract Type A Method ...
└── contract_b/          -> Tests of Contract Type B
└── contract_.../        -> Tests of Contract Type ...
└── conftest.py          -> Common test fixtures
└── utils.py             -> Testing utilities
└── ...
```

### Tests

D-ASA uses the PyTest framework for unit tests and end-to-end tests.

PyTest fixtures are organized hierarchically in the `tests` folder: fixtures defined
in the `conftest.py` file at higher levels are available to all the nested-level
tests.

### Docs

The book is written in [CommonMark](https://commonmark.org/).

The CI pipeline enforces Markdown linting, formatting, and style checking with
[`markdownlint`](https://github.com/DavidAnson/markdownlint).

#### Numbered Lists

Numbered lists **MUST** be defined with `1`-only style.

{{#include ./.include/styles.md:example}}
> ```text
> 1. First item
> 1. Second item
> 1. Third item
> ```
>
> Result:
> 1. First item
> 1. Second item
> 1. Third item

#### Tables

Table rows **MUST** use the same column widths.

{{#include ./.include/styles.md:example}}
> ✅ Correct table format
> ```text
> | Month    | Savings |
> |----------|---------|
> | January  | €250    |
> | February | €80     |
> | March    | €420    |
> ```
>
> ❌ Wrong table format
> ```text
> | Month | Savings |
> |----------|---------|
> | January | €250 |
> | February | €80 |
> | March | €420 |
> ```
>
> Result:
> | Month    | Savings |
> |----------|---------|
> | January  | €250    |
> | February | €80     |
> | March    | €420    |

Consider aligning text in the columns to the left, right, or center by adding a
colon `:` to the left, right, or on both sides of the dashes `---` within the header
row.

{{#include ./.include/styles.md:example}}
> ```text
> | Name   | Quantity | Size |
> |:-------|:--------:|-----:|
> | Item A |    1     |    S |
> | Item B |    5     |    M |
> | Item C |    10    |   XL |
> ```
>
> Result:
> | Name   | Quantity | Size |
> |:-------|:--------:|-----:|
> | Item A |    1     |    S |
> | Item B |    5     |    M |
> | Item C |    10    |   XL |

#### MathJax

Mathematical formulas are defined with [MathJax](https://www.mathjax.org/).

> mdBook MathJax [documentation](https://rust-lang.github.io/mdBook/format/mathjax.html).

#### Block Styles

Block styles are defined in the `./docs/.include/styles.md` file using the mdBook
[include feature](https://rust-lang.github.io/mdBook/format/mdbook.html#including-files).

Block styles (e.g., examples, implementation notes, etc.) are “styled quote” blocks
included in the book.

{{#include ./.include/styles.md:example}}
> This example block has been included with the following syntax:
> ```text
> \{{#include ./.include/styles.md:example}}
> > This example block has been included with the following syntax:
> ```
