# Contributing to D-ASA

Thank you for contributing to D-ASA.

## Prerequisites

The standard contributor workflow assumes:

- [AlgoKit](https://dev.algorand.co/algokit/) for project bootstrap, LocalNet,
  build, and deployment workflows
- [Poetry](https://python-poetry.org/) for the Python environment
- [Docker](https://www.docker.com/) for Algorand LocalNet
- [pre-commit](https://pre-commit.com/) for local checks

Docs contributors also need:

- [Rust and Cargo](https://www.rust-lang.org/tools/install)
- [`mdbook`](https://rust-lang.github.io/mdBook/)
- `mdbook-mermaid`

## Getting Started

### Clone the Repository

```shell
git clone git@github.com:cusma/d-asa.git
cd d-asa
```

### Bootstrap the Development Environment

The standard setup path is:

```shell
algokit project bootstrap all
make pre-commit
make doctor
```

If you are only setting up Python dependencies:

```shell
make install
```

If you are contributing to docs, install the mdBook toolchain as well:

```shell
cargo install mdbook --version 0.5.2 --locked
cargo install mdbook-mermaid --version 0.17.0 --locked
mdbook-mermaid install .
```

### Verify the Environment

Run:

```shell
make doctor
```

`make doctor` runs `algokit doctor`, checks core contributor dependencies, checks
Docker daemon reachability for LocalNet workflows, and warns if docs-only tools
are missing.

## Development Workflow

### Core Commands

The main contributor commands are:

```shell
make help
make build
make test
make test-cov
make lint
make format
make typecheck
make all
```

`make all` runs the standard code quality loop for contributors:

- build smart contracts
- run lint and type checks
- run the default non-showcase test suite

It intentionally does not require mdBook tooling.

### LocalNet Workflow

Start LocalNet when you need end-to-end execution tests or LocalNet deployment:

```shell
make localnet
make deploy-localnet
make showcase
make localnet-stop
```

These targets map to the existing AlgoKit workflow already used by CI and the
project scripts.

### Docs Workflow

For docs editing with live reload:

```shell
make docs-serve
```

For docs validation:

```shell
make docs
```

`make docs` runs both:

- `mdbook build`
- `mdbook test`

## Pull Requests

When preparing a pull request:

1. Keep changes focused and atomic.
1. Add or update tests when behavior changes.
1. Update docs when user-facing behavior, workflows, or interfaces change.
1. Run the relevant local checks before opening the PR.

Suggested pre-PR checklist:

```shell
make doctor
make all
```

If you changed docs:

```shell
make docs
```

If you changed LocalNet behavior or showcase flows:

```shell
make localnet
make showcase
make localnet-stop
```

## Repository Layout

The main top-level layout is:

```text
.algokit/          -> AlgoKit configuration and generators
.github/           -> CI/CD workflows and shared GitHub actions
docs/              -> mdBook source files
modules/           -> D-ASA module implementations
smart_contracts/   -> AVM smart contracts and generated contract artifacts
src/               -> Python-side normalization, helpers, and shared runtime code
tests/             -> SDK, contract, LocalNet, and showcase tests
```

## Style and Quality

### Python

The project uses:

- `black` for formatting
- `ruff` for linting and import organization
- `mypy` for type checking
- `pytest` for tests

Run the standard checks with:

```shell
make format
make lint
make typecheck
make test
```

### Markdown and mdBook

The docs are written in [CommonMark](https://commonmark.org/) and validated in
CI with `markdownlint`, trailing whitespace checks, and `mdbook test`.

#### Numbered Lists

Numbered lists **MUST** use `1.`-only style.

> ```text
> 1. First item
> 1. Second item
> 1. Third item
> ```

#### Tables

Table rows **MUST** keep aligned column widths.

> ✅ Correct table format
> ```text
> | Month    | Savings |
> |----------|---------|
> | January  | EUR 250 |
> | February | EUR 80  |
> | March    | EUR 420 |
> ```
>
> ❌ Wrong table format
> ```text
> | Month | Savings |
> |----------|---------|
> | January | EUR 250 |
> | February | EUR 80 |
> | March | EUR 420 |
> ```

Column alignment may be controlled with `:` markers in the separator row.

#### Admonitions

An admonition is a special type of callout or notice block used to highlight important
information. It is written as a blockquote with a special tag on the first line.

```text
> [!NOTE]
> General information or additional context.

> [!TIP]
> A helpful suggestion or best practice.

> [!IMPORTANT]
> Key information that shouldn't be missed.

> [!WARNING]
> Critical information that highlights a potential risk.

> [!CAUTION]
> Information about potential issues that require caution.
```

#### MathJax

Mathematical formulas are rendered with [MathJax](https://www.mathjax.org/).

Reference:

- [mdBook MathJax documentation](https://rust-lang.github.io/mdBook/format/mathjax.html)

## Additional Notes

- Do not remove or hand-edit generated artifacts under `smart_contracts/artifacts`
  or `src/artifacts` unless the change explicitly requires regenerated output.
- Prefer the checked-in `algokit` commands and `make` targets over ad-hoc local
  command variations so contributor workflows stay aligned with CI.
