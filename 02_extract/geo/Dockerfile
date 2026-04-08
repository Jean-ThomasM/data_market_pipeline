# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
COPY 00_infra/pyproject.toml 00_infra/pyproject.toml
COPY 01_shared/pyproject.toml 01_shared/pyproject.toml
COPY 02_extract/geo/pyproject.toml 02_extract/geo/pyproject.toml
COPY 02_extract/sirene/pyproject.toml 02_extract/sirene/pyproject.toml
COPY 02_extract/france_travail/pyproject.toml 02_extract/france_travail/pyproject.toml

COPY 01_shared/shared 01_shared/shared
COPY 02_extract/geo/config.py 02_extract/geo/config.py
COPY 02_extract/geo/main.py 02_extract/geo/main.py
COPY 02_extract/geo/scraper.py 02_extract/geo/scraper.py

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package geo


FROM python:3.12-slim AS runtime

WORKDIR /app/02_extract/geo

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/01_shared/shared /app/01_shared/shared
COPY --from=builder /app/02_extract/geo/config.py /app/02_extract/geo/config.py
COPY --from=builder /app/02_extract/geo/main.py /app/02_extract/geo/main.py
COPY --from=builder /app/02_extract/geo/scraper.py /app/02_extract/geo/scraper.py

CMD ["python", "main.py"]
