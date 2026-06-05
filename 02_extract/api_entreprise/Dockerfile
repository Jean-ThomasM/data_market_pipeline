# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
COPY 00_infra/pyproject.toml 00_infra/pyproject.toml
COPY 01_shared/pyproject.toml 01_shared/pyproject.toml
COPY 02_extract/adzuna/pyproject.toml 02_extract/adzuna/pyproject.toml
COPY 02_extract/geo/pyproject.toml 02_extract/geo/pyproject.toml
COPY 02_extract/france_travail/pyproject.toml 02_extract/france_travail/pyproject.toml
COPY 02_extract/n8n_trigger/pyproject.toml 02_extract/n8n_trigger/pyproject.toml

COPY 02_extract/api_entreprise/pyproject.toml 02_extract/api_entreprise/pyproject.toml

COPY 01_shared/shared 01_shared/shared
COPY 02_extract/api_entreprise/api.py 02_extract/api_entreprise/api.py
COPY 02_extract/api_entreprise/main.py 02_extract/api_entreprise/main.py

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package api-entreprise


FROM python:3.13-slim AS runtime

WORKDIR /app/02_extract/api_entreprise

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/02_extract/api_entreprise/main.py /app/02_extract/api_entreprise/main.py
COPY --from=builder /app/02_extract/api_entreprise/api.py /app/02_extract/api_entreprise/api.py
COPY --from=builder /app/01_shared/shared /app/01_shared/shared

CMD ["python", "main.py"]
