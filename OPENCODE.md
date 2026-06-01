# data_market_pipeline — Agent Context

## Project Summary

Data engineering pipeline for the French tech job market.
Extracts job offers from France Travail, GEO, Adzuna, and Sirene APIs → stores raw data in GCS → loads into BigQuery → transforms through medallion layers (staging → intermediate → marts) using dbt.

---

## Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| Package manager | uv (workspace, 6 members) |
| Cloud | GCP (BigQuery, GCS, Cloud Run Jobs, Workflows, Secret Manager, Artifact Registry, Cloud Scheduler) |
| IaC | OpenTofu (Terraform-compatible modules) |
| Transformation | dbt-core + dbt-bigquery + dbt-sqlite (local dev) |
| CI/CD | GitHub Actions (Ruff, SQLFluff, dbt parse, TruffleHog, Semantic Release) |
| Containers | Docker multi-stage (uv builder → python:3.12-slim runtime) |

---

## Folder Structure

```
data_market_pipeline/
├── 00_infra/                   # OpenTofu IaC
│   └── opentofu/
│       ├── modules/            # 14 reusable modules
│       └── environments/
│           ├── dev/            # main.tf, schemas/, workflows/*.yaml.tftpl
│           └── prod/
├── 01_shared/                  # Shared Python library
│   └── shared/
│       ├── gcs.py              # GCS read/write/delete helpers
│       └── secrets.py          # Secret Manager access
├── 02_extract/                 # Extract submodules
│   ├── france_travail/         # OAuth2, paginated offers + referentials, NDJSON
│   ├── geo/                    # geo.api.gouv.fr regions/departements/communes
│   ├── adzuna/                 # Adzuna API scraper
│   ├── sirene/                 # Stub (not yet implemented)
│   └── data/                   # Local output (gitignored)
├── 03_transform/               # dbt transformation layer
│   └── dbt/
│       ├── models/
│       │   ├── sources.yml
│       │   └── intermediate_dev/
│       ├── tests/
│       ├── macros/generate_schema_name.sql
│       └── profiles.yml        # bigquery (dev/prod) + sqlite (local)
├── main.py
├── pyproject.toml              # Root workspace
└── .github/workflows/
    ├── ci.yml
    └── release.yml
```

---

## Key Architectural Decisions

1. **Medallion architecture**: raw → staging → intermediate → marts
2. **Dataset naming**: `raw_<env>`, `staging_<env>`, `intermediate_<env>`, `marts_<env>`
3. **Storage abstraction**: `STORAGE=local|gcs` env var — extractors write locally for dev, GCS for prod
4. **Secrets**: Secret Manager in prod, `.env` locally
5. **Dockerfiles**: multi-stage, built from repo root, copying only needed workspace member sources
6. **dbt profiles**: dual-target — BigQuery (dev/prod) and SQLite (local), selected via `DBT_TARGET_ENV`
7. **dbt schema**: custom `generate_schema_name` macro allows explicit schema overrides per model
8. **Orchestration**: Cloud Workflows → Cloud Run Jobs (extract → BQ load → dbt transform), triggered by Cloud Scheduler
9. **uv workspace**: 6 members — `00_infra`, `01_shared`, `france_travail`, `geo`, `sirene`, `adzuna`; all extract submodules depend on `01_shared`
10. **CI**: branch `_*/**` is ignored

---

## Conventions

### Git & commits
- Branches: `feature/*`, `integration`, `main`
- Commits: conventional commits (`feat:`, `chore:`, `fix:`, etc.)

### Python
- Logging: `logging.basicConfig(level=INFO, format="%(asctime)s | %(levelname)s | %(message)s")` in every extract main
- Config objects: `@dataclass`
- Type hints everywhere, no untyped functions
- Lazy `__init__.py` with module docstrings

### SQL (dbt)
- Lowercase keywords
- BigQuery dialect
- 4-space indent
- 120-char max line length
- Model prefixes: `stg_`, `int_`, `mart_`

### GCS paths
- `raw_offres/`, `raw_geo/`, `raw_referentiels/`

### File formats
- NDJSON for streaming records
- JSON for referentials

---

## ❌ NEVER DO — Hard Rules

### Architecture
- **Ne jamais écrire dans BigQuery via des inserts Python** — uniquement via BQ native Load Jobs
- **Ne jamais hardcoder `GCP_PROJECT_ID`** — il est injecté via OpenTofu comme variable d'environnement
- **Ne jamais toucher `prod/`** sans confirmation explicite — toujours travailler dans `dev/` par défaut
- **Ne jamais modifier `01_shared/`** sans vérifier que tous les extracteurs qui en dépendent restent compatibles

### Code quality
- **Ne jamais dupliquer une fonction qui existe déjà dans `01_shared/`** — vérifier `gcs.py` et `secrets.py` avant d'écrire un helper
- **Ne jamais créer une abstraction inutile** — si une fonction fait une seule chose simple, elle n'a pas besoin d'une classe
- **Ne jamais laisser une variable avec un nom générique** : `data`, `result`, `tmp`, `x`, `d` sont interdits

```python
# ❌ Interdit
def process(d, x):
    tmp = d.get(x)
    return tmp

# ✅ Attendu
def get_offer_by_department(offers: list[Offer], department_code: str) -> list[Offer]:
    return [offer for offer in offers if offer.department_code == department_code]
```

- **Ne jamais omettre les type hints** sur les signatures de fonctions
- **Ne jamais écrire de commentaires évidents** — commenter le *pourquoi*, pas le *quoi*

```python
# ❌ Inutile
# On boucle sur les offres
for offer in offers:

# ✅ Utile
# France Travail paginates at 150 results max — we loop until next_page is None
for offer in offers:
```

- **Ne jamais complexifier un script qui peut rester simple** — si une fonction dépasse ~30 lignes, questionner le découpage

### Docker
- **Ne jamais installer de dépendances de dev dans l'image de prod** — `--no-dev` obligatoire avec uv
- **Ne jamais copier le workspace entier** dans le container — uniquement le membre concerné + `01_shared`
- **Toujours utiliser le builder `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`** pour la phase de build
- **Toujours utiliser `python:3.12-slim`** comme image de runtime finale
- **Toujours copier uniquement le virtualenv compilé** du builder vers le runtime — pas les sources uv
- **Toujours placer les layers les plus stables en premier** (base image → deps → code source) pour maximiser le cache Docker

Structure cible d'un Dockerfile extracteur :
```dockerfile
# Stage 1: builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY 01_shared/ ./01_shared/
COPY 02_extract/<extractor>/ ./02_extract/<extractor>/
RUN uv sync --frozen --no-dev --package <extractor>

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY 02_extract/<extractor>/src ./src
ENV PATH="/app/.venv/bin:$PATH"
```

---

## Security

- `.env` et `credentials.json` ne doivent jamais être lus par l'agent (voir `.opencode/ignore`)
- Les secrets sont dans Secret Manager en prod — ne jamais les écrire en dur dans le code ou les configs OpenTofu
- TruffleHog tourne sur chaque PR — tout secret committé bloque le merge

---

## Local Dev Workflow

```bash
# Lancer un extracteur localement
STORAGE=local uv run --package france_travail python -m france_travail.main

# dbt local (SQLite)
DBT_TARGET_ENV=local dbt run --profiles-dir 03_transform/dbt

# Linter
ruff check .
ruff format .
sqlfluff lint 03_transform/dbt/models/
```
