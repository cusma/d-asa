SHELL := /bin/sh

.PHONY: help install install-dev doctor build test test-cov lint format typecheck docs docs-serve pre-commit clean all localnet localnet-stop deploy-localnet showcase jupyter-docker

help:
	@echo "Available targets:"
	@echo "  install         - Install Python dependencies via AlgoKit bootstrap"
	@echo "  install-dev     - Bootstrap the full development environment and install pre-commit hooks"
	@echo "  doctor          - Check contributor dependencies and environment health"
	@echo "  build           - Build smart contracts"
	@echo "  test            - Run the default non-showcase test suite"
	@echo "  test-cov        - Run tests with coverage"
	@echo "  lint            - Run the standard lint and type checks"
	@echo "  format          - Format Python code and auto-fix Ruff issues"
	@echo "  typecheck       - Run mypy"
	@echo "  docs            - Run docs pre-commit checks and mdBook validation"
	@echo "  docs-serve      - Serve mdBook docs locally with live reload"
	@echo "  pre-commit      - Install pre-commit hooks"
	@echo "  clean           - Remove local caches, notebook checkpoints, and ignored build outputs"
	@echo "  all             - Run build, lint, and test"
	@echo "  localnet        - Start AlgoKit LocalNet"
	@echo "  localnet-stop   - Stop AlgoKit LocalNet"
	@echo "  deploy-localnet - Deploy contracts to LocalNet"
	@echo "  showcase        - Run the LocalNet showcase walkthrough"
	@echo "  jupyter-docker  - Start Jupyter Lab in Docker with LocalNet (no local dependencies needed)"

install:
	algokit project bootstrap poetry

install-dev:
	algokit project bootstrap all
	pre-commit install

doctor:
	@set -u; \
	status=0; \
	echo "== AlgoKit doctor =="; \
	algokit doctor || true; \
	echo ""; \
	echo "== D-ASA environment checks =="; \
	check_required() { \
		name="$$1"; \
		cmd="$$2"; \
		if command -v "$$cmd" >/dev/null 2>&1; then \
			echo "[required] $$name: OK ($$(command -v "$$cmd"))"; \
		else \
			echo "[required] $$name: MISSING"; \
			status=1; \
		fi; \
	}; \
	check_optional() { \
		group="$$1"; \
		name="$$2"; \
		cmd="$$3"; \
		hint="$$4"; \
		if command -v "$$cmd" >/dev/null 2>&1; then \
			echo "[$$group] $$name: OK ($$(command -v "$$cmd"))"; \
		else \
			echo "[$$group] $$name: WARN - $$hint"; \
		fi; \
	}; \
	check_required "AlgoKit" algokit; \
	check_required "Poetry" poetry; \
	check_required "pre-commit" pre-commit; \
	if command -v docker >/dev/null 2>&1; then \
		echo "[localnet] Docker CLI: OK ($$(command -v docker))"; \
		if docker info >/dev/null 2>&1; then \
			echo "[localnet] Docker daemon: OK"; \
		else \
			echo "[localnet] Docker daemon: ERROR - Docker is installed but not reachable"; \
			status=1; \
		fi; \
	else \
		echo "[localnet] Docker CLI: ERROR - Docker is required for LocalNet workflows"; \
		status=1; \
	fi; \
	check_optional "docs" "Cargo" cargo "install Rust/Cargo to work on docs"; \
	check_optional "docs" "mdBook" mdbook "install with: cargo install mdbook --version 0.5.2 --locked"; \
	check_optional "docs" "mdBook Mermaid" mdbook-mermaid "install with: cargo install mdbook-mermaid --version 0.17.0 --locked"; \
	exit $$status

build:
	algokit project run build

test:
	algokit project run test

test-cov:
	poetry run pytest --cov=src --cov=smart_contracts --cov=modules --cov-report=term-missing -m "not showcase"

lint:
	algokit project run lint

format:
	poetry run black .
	poetry run ruff check --fix .

typecheck:
	poetry run mypy

docs:
	mdbook-mermaid install .
	pre-commit run --all-files mdbook-build
	pre-commit run --all-files mdbook-test
	pre-commit run --all-files markdownlint
	pre-commit run --all-files trailing-whitespace

docs-serve:
	mdbook-mermaid install .
	mdbook serve --open

pre-commit:
	pre-commit install

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage htmlcov book mermaid-init.js mermaid.min.js
	find . -type d \( -name __pycache__ -o -name '.ipynb_checkpoints' \) -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

all: build lint test

localnet:
	algokit localnet start

localnet-stop:
	algokit localnet stop

deploy-localnet:
	algokit project deploy localnet

showcase:
	poetry run pytest -s -v -m showcase tests/pam/test_pam_lifecycle_showcase.py

jupyter-docker:
	./d-asa jupyter

