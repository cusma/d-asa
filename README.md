# Debt Algorand Standard Application (D-ASA)

D-ASA is a full tokenization framework for [ACTUS](https://www.actusfrf.org/)-compliant
debt instruments, issued and executed on the Algorand Virtual Machine.

```mermaid
flowchart LR
  ACTUS["ACTUS Contract"] --> NORMALIZE["AVM Normalization"]
  NORMALIZE --> ABI["ABI Upload"]
  ABI --> EXEC["AVM Execution"]
```

The canonical ABI artifact is:

- `src/artifacts/DASA.arc56.json`

Documentation: <https://cusma.github.io/d-asa/>

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/cusma/d-asa)

## Demo in One Command

The fastest way to showcase D-ASA is with host AlgoKit for Algorand LocalNet and
Docker for the showcase runtime.

- Install [AlgoKit](https://dev.algorand.co/algokit/algokit-intro/#cross-platform-installation)
- Install [Docker](https://docs.docker.com/get-docker/)

```shell
git clone git@github.com:cusma/d-asa.git
cd d-asa
./d-asa run
```

What `./d-asa run` does:

- builds the local demo image
- starts host AlgoKit LocalNet if it is not already running
- waits for the LocalNet services required by the showcase
- runs the PAM fixed coupon and zero coupon showcase walkthroughs
- leaves LocalNet running so the Lora transaction links remain explorable

When you are finished inspecting the links:

```shell
algokit localnet stop
```

Open the published docs with:

```shell
./d-asa docs
```

If you want the exact `d-asa ...` syntax in your current shell, you can add an alias:

```shell
alias d-asa="$PWD/d-asa"
```

If browser launch is not wanted:

```shell
D_ASA_NO_OPEN=1 ./d-asa docs
```

Notes:

- targets macOS and Linux
- requires both Docker and AlgoKit on the host
- the demo joins the LocalNet Docker network when available, which keeps the showcase
on direct container-to-container networking

## Development

The D-ASA project is developed with [AlgoKit](https://algorand.co/algokit) and [Poetry](https://python-poetry.org/).

Bootstrap the development environment:

```shell
make install-dev
```

Verify your environment:

```shell
make doctor
```

See the available contributor commands:

```shell
make help
```

Start your Algorand LocalNet:

```shell
make localnet
```

Run the default test suite:

```shell
make test
```

Build smart contracts:

```shell
make build
```

Run the showcase tests directly:

```shell
make showcase
```

Serve docs locally with live reload:

```shell
make docs-serve
```

## Contributing

Contributor setup and workflow guidance live in [CONTRIBUTING.md](./CONTRIBUTING.md).
