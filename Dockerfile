FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV HOME=/home/dasa
ENV XDG_CONFIG_HOME=/home/dasa/.config
ENV XDG_DATA_HOME=/home/dasa/.local/share
ENV XDG_STATE_HOME=/home/dasa/.local/state

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        docker.io \
        docker-compose \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        algokit==2.10.2 \
        poetry==2.1.4

WORKDIR /workspace

COPY pyproject.toml poetry.lock ./

RUN mkdir -p "$HOME" \
    && poetry install --without dev --no-root --no-ansi
