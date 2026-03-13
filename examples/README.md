# Notebook Examples

This folder contains two live LocalNet walkthroughs:

- `pam_fixed_coupon_bond.ipynb`
- `pam_zero_coupon_bond.ipynb`

They are intended to be run from the repository root and rerun from top to bottom
against a fresh AlgoKit LocalNet.

## Quick Start (Docker - No Local Dependencies)

The easiest way to run the notebooks is using Docker:

```shell
./d-asa jupyter
```

Or via make:

```shell
make jupyter-docker
```

This will:
- Build the Docker image with all dependencies
- Start AlgoKit LocalNet if needed
- Launch Jupyter Lab at http://localhost:8888
- Automatically configure LocalNet connectivity

Then open one of the notebooks in the `examples/` folder.

Press Ctrl+C to stop Jupyter Lab when finished.

## Alternative: Local Setup (Requires Local Dependencies)

If you prefer running Jupyter locally, follow these steps:

Bootstrap the full development environment:

```shell
make install-dev
```

If you prefer the raw AlgoKit command, the equivalent bootstrap is:

```shell
algokit bootstrap all
```

Install the optional notebook dependencies:

```shell
poetry install --with notebooks
```

Start LocalNet:

```shell
make localnet
```

or:

```shell
algokit localnet start
```

Launch Jupyter from the repository root:

```shell
poetry run jupyter lab examples/
```

Then open one of the notebooks in `examples/`.

## Notes

- The notebooks perform real deployment and execution against LocalNet.
- Both notebooks assume the kernel is started from this repository checkout.
- If a prior run leaves LocalNet in an unexpected state, restart it and rerun the
  notebook from the first cell.
- The notebooks are committed without outputs so each run shows fresh LocalNet data.
