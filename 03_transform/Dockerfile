# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system \
        dbt-bigquery>=1.10.2 \
        dbt-core>=1.11.8 \
        dbt-sqlite>=1.10.0

COPY 03_transform/dbt /app/dbt

ENV DBT_PROFILES_DIR=/app/dbt

WORKDIR /app/dbt

CMD ["dbt", "run", "--project-dir", "/app/dbt", "--profiles-dir", "/app/dbt", "--target", "dev"]
