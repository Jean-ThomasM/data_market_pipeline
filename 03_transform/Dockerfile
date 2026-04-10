# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Initialiser l'environnement Python du projet et ajouter dbt.
COPY 03_transform/pyproject.toml /app/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv add dbt-core dbt-bigquery && \
    uv sync --no-dev

# Copier la configuration dbt.
COPY 03_transform/dbt /app/dbt

ENV DBT_PROFILES_DIR=/app/dbt

WORKDIR /app/dbt

CMD ["uv", "run", "dbt", "--version"]
