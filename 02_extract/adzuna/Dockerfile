# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Copy metadata first to maximize Docker layer cache reuse.
COPY pyproject.toml uv.lock ./
COPY 00_infra/pyproject.toml 00_infra/pyproject.toml
COPY 01_shared/pyproject.toml 01_shared/pyproject.toml
COPY 02_extract/adzuna/pyproject.toml 02_extract/adzuna/pyproject.toml
COPY 02_extract/france_travail/pyproject.toml 02_extract/france_travail/pyproject.toml
COPY 02_extract/geo/pyproject.toml 02_extract/geo/pyproject.toml
COPY 02_extract/sirene/pyproject.toml 02_extract/sirene/pyproject.toml

# Copy only the packages needed by the Adzuna extractor.
COPY 01_shared/shared 01_shared/shared
COPY 02_extract/adzuna/config.py 02_extract/adzuna/config.py
COPY 02_extract/adzuna/main.py 02_extract/adzuna/main.py
COPY 02_extract/adzuna/scraper.py 02_extract/adzuna/scraper.py
COPY 02_extract/adzuna/scraper_2.py 02_extract/adzuna/scraper_2.py
COPY 02_extract/adzuna/utils.py 02_extract/adzuna/utils.py

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package adzuna


FROM python:3.12-alpine AS runtime

WORKDIR /app/02_extract/adzuna

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/01_shared/shared /app/01_shared/shared
COPY --from=builder /app/02_extract/adzuna/config.py /app/02_extract/adzuna/config.py
COPY --from=builder /app/02_extract/adzuna/main.py /app/02_extract/adzuna/main.py
COPY --from=builder /app/02_extract/adzuna/scraper.py /app/02_extract/adzuna/scraper.py
COPY --from=builder /app/02_extract/adzuna/scraper_2.py /app/02_extract/adzuna/scraper_2.py
COPY --from=builder /app/02_extract/adzuna/utils.py /app/02_extract/adzuna/utils.py

CMD ["python", "main.py"]
