# AGENTS.md

## Setup & workspace

```bash
uv sync --dev                        # install all workspace members + dev deps
uv sync --dev --package france-travail  # install a single workspace member
```

5 workspace members in `pyproject.toml`: `00_infra`, `01_shared`, `france_travail`, `geo`, `adzuna`. Extract modules depend on `shared` via `[tool.uv.sources]` pointing to workspace.

## Lint & verify (run in order)

```bash
uv run ruff check .                  # Python lint
uv run dbt parse --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt --target local  # dbt syntax + graph validation
uv run sqlfluff lint 03_transform/dbt/models --dialect bigquery  # SQL lint
uv run pre-commit run --all-files    # pre-commit (ruff --fix + ruff-format)
```

No test framework, no typecheck configured. CI runs at PR time vs `main`/`integration`. Pre-commit excludes `_old/` and `_developpements/`.

## Run extractors locally

Set `STORAGE=local`. Data lands in `02_extract/data/`.

```bash
# France Travail (requires FT_CLIENT_ID, FT_CLIENT_KEY)
FT_EXTRACT_TARGET=offers uv run python 02_extract/france_travail/main.py
FT_EXTRACT_TARGET=referentials uv run python 02_extract/france_travail/main.py
FT_EXTRACT_TARGET=all uv run python 02_extract/france_travail/main.py

# GEO (no auth needed)
uv run python 02_extract/geo/main.py
```

In GCS mode (`STORAGE=gcs`), credentials come from Secret Manager (not `.env`).

## Docker

Build from **repo root**, not from subdirectory:

```bash
docker build -f 02_extract/france_travail/Dockerfile -t extract-ft:local .
docker build -f 02_extract/geo/Dockerfile -t extract-geo:local .
docker build -f 03_transform/Dockerfile -t dbt-transform:local .
```

Multi-stage build copies only the needed workspace member sources. Uses `uv sync --frozen --no-dev --package <name>`.

## dbt

- **local** target: SQLite (file-based, no cloud needed)
- **dev** target: BigQuery (oauth, project `data-market-386959`)
- Selected via `DBT_TARGET_ENV` env var (default `local`)

```bash
export DBT_TARGET_ENV=local
uv run dbt run --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt
```

SQL style (enforced by `.sqlfluff`): lowercase keywords, BigQuery dialect, 4-space indent, 120-char lines.

## Storage abstraction

`STORAGE=local|gcs` controls output backend in all extractors. Every scraper has dual-path save logic in `utils.py`: writes to GCS if `gcs`, to `02_extract/data/` otherwise.

## Infra (OpenTofu)

14 reusable modules under `00_infra/opentofu/modules/`. Environments in `00_infra/opentofu/environments/{dev,prod}/`. IaC provisions GCS, BigQuery datasets/tables, Cloud Run Jobs, Workflows, Secret Manager secrets, service accounts, IAM.

## Stale/slow areas

- `sirene/` extract module: stub only (`print("Hello from sirene!")`)
- `adzuna/` has two scraper files (`scraper.py`, `scraper_2.py`)
- `00_infra/src/` and `03_transform/src/` are minimal/empty packages

## Git conventions

- Conventional commits (`feat:`, `chore:`, etc.)
- Branches: `feature/*`, `integration`, `main`
- `.gitignore`: `*.json`, `*.ndjson`, `*.parquet`, `*.tfvars`, `_old/`, `.qwen/`
