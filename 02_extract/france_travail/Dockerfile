# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Les fichiers de métadonnées sont copiés en premier afin de maximiser
# la réutilisation du cache Docker lorsque seule l'implémentation change.
COPY pyproject.toml uv.lock ./
COPY 00_infra/pyproject.toml 00_infra/pyproject.toml
COPY 01_shared/pyproject.toml 01_shared/pyproject.toml
COPY 02_extract/geo/pyproject.toml 02_extract/geo/pyproject.toml
COPY 02_extract/sirene/pyproject.toml 02_extract/sirene/pyproject.toml
COPY 02_extract/france_travail/pyproject.toml 02_extract/france_travail/pyproject.toml

# Les sources nécessaires au package cible sont copiées après les métadonnées.
COPY 01_shared/shared 01_shared/shared
COPY 02_extract/france_travail/auth.py 02_extract/france_travail/auth.py
COPY 02_extract/france_travail/config.py 02_extract/france_travail/config.py
COPY 02_extract/france_travail/ft_api.py 02_extract/france_travail/ft_api.py
COPY 02_extract/france_travail/scraper.py 02_extract/france_travail/scraper.py
COPY 02_extract/france_travail/utils.py 02_extract/france_travail/utils.py

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package france-travail


FROM python:3.12-slim AS runtime

WORKDIR /app/02_extract/france_travail

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/02_extract/france_travail/auth.py /app/02_extract/france_travail/auth.py
COPY --from=builder /app/02_extract/france_travail/config.py /app/02_extract/france_travail/config.py
COPY --from=builder /app/02_extract/france_travail/ft_api.py /app/02_extract/france_travail/ft_api.py
COPY --from=builder /app/02_extract/france_travail/scraper.py /app/02_extract/france_travail/scraper.py
COPY --from=builder /app/01_shared/shared app/01_shared/shared
COPY --from=builder /app/02_extract/france_travail/utils.py app/02_extract/france_travail/utils.py

EXPOSE 8000

CMD ["uvicorn", "ft_api:app", "--host", "0.0.0.0", "--port", "8000"]
