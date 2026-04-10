# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dependances verrouillees du projet (dont dbt-bigquery).
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copier la configuration dbt.
COPY dbt /app/dbt

ENV DBT_PROFILES_DIR=/app/dbt

WORKDIR /app/dbt

CMD ["uv", "run", "dbt", "run", "--project-dir", "/app/dbt", "--profiles-dir", "/app/dbt", "--target", "dev"]
