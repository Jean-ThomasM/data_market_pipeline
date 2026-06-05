# Documentation Exhaustive — Data Market Pipeline

> Pipeline ELT serverless sur GCP — Analyse du marché de l'emploi Data en France.
>
> **Auteur** : Jean-Thomas Miquelot
> **Stack** : Python 3.13 + dbt + BigQuery + GCP serverless + OpenTofu

---

## Table des Matières

1. [Présentation Générale](#1-présentation-générale)
2. [Data Lineage](#2-data-lineage)
3. [Architecture Technique](#3-architecture-technique)
4. [Sécurité](#4-sécurité)
5. [CI/CD](#5-cicd)
6. [Monitoring & Observabilité](#6-monitoring--observabilité)
7. [KPI & Métriques](#7-kpi--métriques)
8. [Infrastructure as Code (IaC)](#8-infrastructure-as-code-iac)
9. [Data Catalog](#9-data-catalog)
10. [Extracteurs — Détail par Source](#10-extracteurs--détail-par-source)
11. [Transformations dbt — Medallion](#11-transformations-dbt--medallion)
12. [Coûts & FinOps](#12-coûts--finops)
13. [n8n & Scraping societe.com](#13-n8n--scraping-societecom)
14. [Environnements](#14-environnements)
15. [Gouvernance des Données](#15-gouvernance-des-données)
16. [Annexes](#16-annexes)

---

## 1. Présentation Générale

### 1.1 Contexte Métier

**DataTalent** est une startup spécialisée dans l'analyse du marché de l'emploi tech. Ce pipeline industrialise la collecte et la transformation de données pour répondre à la question :

> **Où recrute-t-on des profils Data (Data Engineers) en France, dans quelles entreprises, et à quels salaires ?**

### 1.2 Sources de Données

| Source | Type | Authentification | Volume | Fréquence |
|--------|------|-----------------|--------|-----------|
| France Travail (API offres v2) | Offres d'emploi | OAuth2 (client credentials) | ~15k/jour | Quotidienne |
| Adzuna (API Search) | Offres d'emploi | App ID + API Key | ~5k/jour | Quotidienne |
| geo.api.gouv.fr | Référentiel géographique | Publique (aucune) | Statique | Annuelle |
| recherche-entreprises.api.gouv.fr | Enrichissement corporate | Publique (rate-limitée) | À la demande | Temps réel |
| societe.com (via n8n) | Scraping HTML | Aucune (proxy HTTP) | Variable | Post-dbt |

### 1.3 Stack Technologique

| Couche | Technologie | Justification |
|--------|------------|---------------|
| Langage | Python 3.13 | Écosystème data mature |
| Package manager | uv | 10-100x plus rapide que pip |
| Data warehouse | BigQuery | Serverless, séparation stockage/calcul |
| Transformation | dbt-core | Versionné, testable, documenté |
| Orchestration | GCP Workflows | Serverless, pas de cluster à gérer |
| Calcul serverless | Cloud Run Jobs | Scale-to-zero, pay-per-use |
| Stockage objet | GCS | Data Lake, lifecycle policies |
| Secrets | Secret Manager | Gestion centralisée, IAM intégré |
| CI/CD | GitHub Actions + WIF | OIDC, pas de secrets long-lived |
| IaC | OpenTofu | Open-source Terraform fork |
| Monitoring | Cloud Monitoring | Natif GCP, alerting intégré |
| BI | Looker Studio | Gratuit, connecté à BigQuery |
| Scraping | n8n + Python | Workflow visuel + fallback direct |

---

## 2. Data Lineage

### 2.1 Vue d'Ensemble du Flux de Données

```
APIs Externes
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTRACTION (Cloud Run Jobs)                │
│  extract-ft  extract-geo  extract-adzuna  api-entreprise    │
│  n8n-trigger (via n8n proxy ou fallback HTTP direct)        │
└─────────────────────────────────────────────────────────────┘
    │  NDJSON / JSON
    ▼
┌─────────────────────────────────────────────────────────────┐
│              DATA LAKE (GCS)                                 │
│  gs://{project}-data-lake-{env}/raw/{source}/*.ndjson       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              LOAD (GCP Workflows → BQ Load Jobs)             │
│  Schema explicite, autodetect = false, aucune transformation │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│   BigQuery STAGING (Bronze)                                  │
│   staging_offres_ft       staging_offres_adzuna              │
│   staging_regions/departements/communes/epcis                │
│   staging_api_entreprise  staging_n8n_societe                │
│   staging_societe_tracking                                   │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│   dbt — INTERMEDIATE (Silver)                                │
│   int_geo_communes        int_ft_employer_names              │
│   int_ft_offres           int_adzuna_offres                  │
│   int_adzuna_enrichissement                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│   dbt — MARTS (Gold)                                         │
│   mart_offres_data_jobs   mart_recrutement_geographique      │
│   mart_recruteurs         mart_employeurs_corporate          │
│   mart_salaires           mart_finops_costs                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│   CONSOMMATION (Looker Studio)                               │
│   Dashboard métier + Dashboard FinOps                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Lignage Détaillé (Table par Table)

#### France Travail → Marts

```
staging_offres_ft
    ├──→ int_ft_employer_names (enrichissement nom employeur)
    │       └── lookup dictionnaire + regex fallback
    └──→ int_ft_offres
            ├── JOIN int_geo_communes (code commune INSEE)
            ├── JOIN int_ft_employer_names (offer_id)
            ├── FILTER rome_codes IN (data métiers)
            ├── DEDUP ROW_NUMBER() OVER (offer_id)
            └──→ mart_offres_data_jobs (UNION ALL Adzuna)
                    ├──→ mart_recrutement_geographique
                    ├──→ mart_recruteurs
                    └──→ mart_salaires
```

#### Adzuna → Marts

```
staging_offres_adzuna
    └──→ int_adzuna_offres
            ├── JOIN int_geo_communes (3 niveaux de fallback)
            │   1. Exact match: city_name = commune_nom
            │   2. Textuel: location_display_name LIKE commune
            │   3. Coordonnées: distance euclidienne min
            ├── FILTER titre LIKE data keywords
            ├── DEDUP ROW_NUMBER() OVER (offer_id)
            └──→ int_adzuna_enrichissement
                    ├── LEFT JOIN staging_api_entreprise (employer, commune)
                    │   SIREN, finances, dirigeants, egapro, ESS
                    ├── LEFT JOIN staging_n8n_societe (employer, commune)
                    │   capital social, convention collective, CA, effectif
                    └──→ mart_offres_data_jobs
                            ├──→ mart_recrutement_geographique
                            ├──→ mart_recruteurs
                            ├──→ mart_employeurs_corporate
                            └──→ mart_salaires
```

#### Référentiel Géo

```
staging_regions ─┐
staging_departements ─┤
staging_communes ─────┤──→ int_geo_communes (consolidation postale)
staging_epcis ────────┘       │
                        ├──→ int_ft_offres
                        └──→ int_adzuna_offres
```

#### Enrichissement Corporate (API Entreprise + n8n)

```
int_adzuna_offres ──→ api-entreprise (Cloud Run Job)
    │                    │  recherche-entreprises.api.gouv.fr
    │                    │  search_by_name_city()
    │                    ▼
    │               staging_api_entreprise (SIREN, finances, dirigeants)
    │                    │
    │               n8n-trigger (Cloud Run Job)
    │                    │  Query BQ: int_adzuna_offres LEFT JOIN api_entreprise
    │                    │  WHERE NOT IN staging_societe_tracking
    │                    │
    │                    ├─(priorité)──→ n8n (Cloud Run Service)
    │                    │                    └──→ societe.com GET HTML
    │                    └─(fallback)──→ scraper.scrape_societe() (direct HTTP)
    │                    │
    │                    ▼
    │               GCS → staging_n8n_societe
    │                    │
    └────────────────────┤
                         ▼
               int_adzuna_enrichissement (dbt SQL JOIN)
                         │
                         └──→ mart_employeurs_corporate
                         └──→ mart_offres_data_jobs (columnes enrichies)
```

### 2.3 Clés de Jointure Inter-Sources

| Jointure | Type | Clé | Méthode |
|----------|------|-----|---------|
| FT ↔ Géo | Déterministe | `commune_code` (INSEE) | INNER JOIN direct |
| Adzuna ↔ Géo | Probabiliste (3 niveaux) | `city_name` / `location_display_name` / coordonnées GPS | LEFT JOIN avec fallbacks |
| FT ↔ SIRENE | Noms normalisés | `employer_name` + commune | API lookup |
| Adzuna ↔ API Entreprise | Déterministe | `LOWER(TRIM(employer_name))` + `LOWER(TRIM(nom_commune))` | LEFT JOIN |
| Adzuna ↔ n8n societe | Déterministe | `LOWER(TRIM(employer_name))` + `LOWER(TRIM(nom_commune))` | LEFT JOIN (SIREN fait pont) |

---

## 3. Architecture Technique

### 3.1 Diagramme d'Architecture

```mermaid
flowchart TD
    Scheduler[Cloud Scheduler] ➔|Déclenchement quotidien| Workflow[Cloud Workflows]

    subgraph Ingestion [Ingestion & Chargement]
        job_ft[extract-ft-dev]
        job_geo[extract-geo-dev]
        job_adz[extract-adzuna-dev]
        job_api[api-entreprise-dev]
    end

    Workflow ➔|1. Lance les Jobs en parallèle| Ingestion

    API_FT[API France Travail] ➔|OAuth2| job_ft
    API_GEO[API Géo Gouv] ➔|Public| job_geo
    API_ADZ[API Adzuna] ➔|API Key| job_adz
    API_ENT[API Recherche Entreprises] ➔|Public| job_api

    bucket[GCS Data Lake]
    job_ft ➔|NDJSON| bucket
    job_geo ➔|JSON| bucket
    job_adz ➔|NDJSON| bucket
    job_api ➔|NDJSON| bucket

    Workflow ➔|2. BQ Load Jobs| BQLoad[BigQuery Load Jobs]
    bucket ➔|Chargement brut| BQLoad

    subgraph BigQuery [BigQuery]
        bq_raw[staging_*]
        bq_int[int_*]
        bq_marts[mart_*]
    end

    BQLoad ➔ bq_raw
    job_dbt[dbt-run-dev] ➔|3. Transform| bq_int
    job_dbt ➔ bq_marts
    bq_raw ➔ job_dbt

    subgraph n8n_flow [Scraping societe.com]
        job_n8n_trig[n8n-trigger-dev]
        n8n_proxy[n8n-dev]
        web_societe[societe.com]
    end

    Workflow ➔|4. Scraping| job_n8n_trig
    bq_int ➔|Offres non traitées| job_n8n_trig
    job_n8n_trig ➔|Webhook POST| n8n_proxy
    n8n_proxy ➔|Scrape HTML| web_societe
    n8n_proxy ➔|NDJSON| bucket
    Workflow ➔|5. Load n8n| load_n8n
    bucket ➔ load_n8n ➔|staging_n8n_societe| bq_raw

    Dashboard[Dashboard Looker Studio] ➔ bq_marts
```

### 3.2 Services GCP Utilisés

| Service | Rôle | Configuration |
|---------|------|--------------|
| **Cloud Run Jobs** | Exécution des extracteurs Python + dbt | 1 vCPU, 512 MiB, scale-to-zero |
| **Cloud Run Service** | n8n (proxy scraping) | 1 CPU, 2 Gi, 1 instance manuelle |
| **Cloud Workflows** | Orchestration du pipeline | Workflow YAML, étapes parallèles |
| **Cloud Scheduler** | Déclenchement quotidien | 3 crons (FT 6h, GEO lundi 5h, Adzuna 7h) |
| **BigQuery** | Data warehouse Medallion | Datasets: staging, intermediate, marts, finops |
| **GCS** | Data Lake | Versioning activé, lifecycle policies |
| **Secret Manager** | Stockage des credentials | 6 secrets, accès IAM |
| **Artifact Registry** | Registry Docker | Région europe-west1 |
| **Cloud Monitoring** | Alerting + Dashboard | Uptime checks, log metrics, 4 alert policies |

### 3.3 Séquence d'Exécution

```
06:00  Cloud Scheduler → pipeline-global-dev (Workflow)
        │
        ├── Parallel:
        │   ├── extract-ft-dev (Cloud Run Job)
        │   ├── extract-geo-dev (Cloud Run Job)
        │   ├── extract-adzuna-dev (Cloud Run Job)
        │   ├── api-entreprise-dev (Cloud Run Job)
        │   └── n8n-trigger-dev (Cloud Run Job)
        │
        ├── Sequential (après extract):
        │   ├── load-staging-offres-ft (Workflow)
        │   ├── load-staging-geo (Workflow)
        │   ├── load-staging-adzuna (Workflow)
        │   ├── load-staging-api-entreprise (Workflow)
        │   └── load-staging-n8n-societe (Workflow)
        │
        ├── dbt-run-dev (Cloud Run Job)
        │
        └── Done
```

---

## 4. Sécurité

### 4.1 Principe du Moindre Privilège (IAM)

Quatre service accounts distincts, chacun avec les droits minimaux nécessaires :

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Accounts                          │
├─────────────────────────────────────────────────────────────┤
│ pipeline-runner-dev  → exécute extracteurs + workflows       │
│ dbt-runner-dev       → exécute dbt sur BigQuery             │
│ n8n-runner-dev       → exécute le service n8n               │
│ github-ci-cd-dev     → utilisé par GitHub Actions (WIF)     │
└─────────────────────────────────────────────────────────────┘
```

#### pipeline-runner-dev (droits effectifs)

| Ressource | Rôle | Périmètre |
|-----------|------|-----------|
| GCS | `storage.objectAdmin` | Bucket data-lake |
| BigQuery | `dataEditor` + `jobUser` | Tous datasets |
| Secret Manager | `secretAccessor` | Tous secrets |
| Cloud Run | `jobsExecutor` + `developer` + `viewer` | Projet |
| Workflows | `invoker` | Projet |

#### dbt-runner-dev

| Ressource | Rôle | Périmètre |
|-----------|------|-----------|
| BigQuery | `dataEditor` + `jobUser` | Projet |
| Secret Manager | `secretAccessor` | Projet |
| Billing (optionnel) | `dataViewer` | Dataset billing |

#### n8n-runner-dev

| Ressource | Rôle | Périmètre |
|-----------|------|-----------|
| GCS | `storage.objectViewer` | Bucket data-lake |
| BigQuery | `dataEditor` + `jobUser` | Dataset staging |
| Secret Manager | `secretAccessor` | Secret encryption key |
| Public | `run.invoker` (allUsers) | Service n8n (webhook HTTP) |

### 4.2 Gestion des Secrets

Tous les secrets sont stockés dans **Secret Manager**, jamais dans le code :

| Secret | Utilisé par |
|--------|-------------|
| `FT_CLIENT_ID` | extract-ft (OAuth2) |
| `FT_CLIENT_KEY` | extract-ft (OAuth2) |
| `ADZUNA_API_ID` | extract-adzuna (App ID) |
| `ADZUNA_API_KEY` | extract-adzuna (API Key) |
| `DBT_ENV_SECRET` | dbt-runner |
| `n8n-encryption-key-dev` | n8n service |

**Mode local** (STORAGE=local) : les secrets sont lus depuis `.env`.
**Mode cloud** (STORAGE=gcs) : les secrets sont lus depuis Secret Manager via l'API.

### 4.3 Workload Identity Federation (WIF)

GitHub Actions s'authentifie via **OIDC** — pas de clé de service stockée dans GitHub :

```
GitHub Actions → OIDC Token → GCP WIF Pool → Service Account Impersonation
```

Configuration :
- **Pool** : `github-pool-dev`
- **Provider** : `github-provider-dev`
- **Attribut** : `attribute.repository/Jean-ThomasM/data_market_pipeline`
- **SA cible** : `github-ci-cd-dev@data-market-386959.iam.gserviceaccount.com`

### 4.4 Sécurité du Code

| Mesure | Outil | Déclencheur |
|--------|-------|-------------|
| Scan de secrets | TruffleHog | Chaque PR (CI) |
| Lint Python | Ruff | Pre-commit + CI |
| Formatage | Ruff format | Pre-commit + CI |
| Lint SQL | SQLFluff | CI |
| Validation dbt | dbt parse | CI |

### 4.5 Sécurité des Données

| Tag de Sensibilité | Tables concernées | Mesures |
|--------------------|-------------------|---------|
| `SENSITIVE_PII` | `staging_offres_ft` (URL contact employeur) | Accès limité, pas d'export |
| `GEOLOCATION` | `staging_offres_ft`, `staging_offres_adzuna` (coordonnées) | Données agrégées dans les marts |
| `PUBLIC` | Données géo, SIRENE, API Entreprise | Aucune restriction |

### 4.6 Sécurité Réseau

- **n8n** : accessible publiquement (webhook POST depuis Cloud Run Job)
- **BigQuery** : accès via IAM, pas d'IP filtering (pas de VPC nécessaire)
- **Cloud Run Jobs** : internes, pas d'ingress public
- **Secret Manager** : accessible uniquement via API avec IAM

---

## 5. CI/CD

### 5.1 Workflows GitHub Actions

#### CI — Tests & Sécurité (`ci.yml`)

Déclencheurs : PR vers `main`/`integration`, push sur `integration`

```
┌─────────────────┐
│   TruffleHog    │  Scan de secrets
├─────────────────┤
│   uv sync       │  Installation dépendances
├─────────────────┤
│   Ruff check    │  Lint Python
├─────────────────┤
│   Ruff format   │  Vérification formatage
├─────────────────┤
│   pytest        │  Tests unitaires
├─────────────────┤
│   dbt parse     │  Validation graphe SQL
├─────────────────┤
│   SQLFluff lint │  Lint SQL (dialect BigQuery)
└─────────────────┘
```

**Exclusions** : `_old/` et `_developpements/` (path-ignore)

#### dbt CI (`dbt-ci.yml`)

Déclencheurs : PR/push sur `main`/`integration` avec modifications dans `03_transform/dbt/`

```
┌─────────────────────────┐
│   WIF Authentication    │  OIDC → GCP
├─────────────────────────┤
│   Create ephemeral BQ   │  Dataset: ci_pr_{number}
├─────────────────────────┤
│   dbt run               │  Exécution sur BQ éphémère
├─────────────────────────┤
│   dbt test              │  Tests unitaires SQL
├─────────────────────────┤
│   Cleanup datasets      │  TOUJOURS exécuté (if: always())
└─────────────────────────┘
```

**Cleanup garanti** : même en cas d'échec, les datasets BQ éphémères sont supprimés.

#### Release — Build, Deploy & Release (`release.yml`)

Déclencheurs : PR, push `main`/`integration`, `workflow_dispatch`

```
┌─────────────────────────┐
│   Path filter           │  Détection des composants modifiés
│   (dorny/paths-filter)  │  shared, ft, geo, adzuna, api_entreprise,
│                         │  n8n_trigger, n8n, dbt
├─────────────────────────┤
│   Semantic Release      │  Versioning automatique (push main)
├─────────────────────────┤
│   Build & Push Docker   │  Pour chaque composant modifié :
│                         │  - Tag env (dev/prod)
│                         │  - Tag version semver (main)
│                         │  - Tag latest (main)
│                         │  - Docker Buildx + GHA cache
├─────────────────────────┤
│   Promote (man.)        │  Retag dev → prod (workflow_dispatch)
├─────────────────────────┤
│   Tofu apply            │  Déploiement IaC dans l'environnement
└─────────────────────────┘
```

**Tags Docker** :
- `{composant}:dev` (branche integration)
- `{composant}:prod` (branche main)
- `{composant}:{version}` (semver, ex: 1.2.3)
- `{composant}:latest` (branche main)

### 5.2 Pre-commit Hooks (Local)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff          # --fix
      - id: ruff-format
```

Exclusions : `_old/`, `_developpements/`

### 5.3 Pipeline de Vérification Locale

```bash
# Ordre d'exécution recommandé
uv run ruff check .                                    # 1. Lint Python
uv run dbt parse --project-dir 03_transform/dbt ...    # 2. Validation dbt
uv run sqlfluff lint 03_transform/dbt/models ...       # 3. Lint SQL
uv run pre-commit run --all-files                      # 4. Pre-commit hooks
```

### 5.4 Stratégie de Branches

```
main ──────────────────────────── (déploiement prod)
    ↕                                          ↕
integration ─────────────────────── (déploiement dev)
    ↕
feature/* (PR → integration)

Conventions : conventional commits (feat:, chore:, fix:, etc.)
```

---

## 6. Monitoring & Observabilité

### 6.1 Logging Applicatif

**Module** : `01_shared/shared/logging_config.py`

Deux formats disponibles via variable d'environnement `LOG_FORMAT` :

| Format | Description | Utilisation |
|--------|-------------|-------------|
| Standard (défaut) | `%(asctime)s \| %(levelname)s \| %(name)s \| %(message)s` | Développement local |
| Structuré (JSON-like) | `{"timestamp": ..., "level": ..., "message": ...}` | Production (Cloud Logging) |

Activation du format structuré :
```python
from shared.logging_config import configure_structured_logging
logger = configure_structured_logging()
```

Niveaux configurables via `LOG_LEVEL` (défaut: INFO).

### 6.2 Métriques Applicatives

**Module** : `01_shared/shared/metrics.py`

#### MetricsCollector

Utilisé par tous les extracteurs pour collecter des métriques d'exécution :

```python
collector = MetricsCollector("extract-ft")

call = collector.start_api_call("/offres/search")
# ... appel API ...
call.complete(success=True, status_code=200, records_count=50)

summary = collector.finalize(records_saved=950, duplicates=50)
```

Métriques collectées par extraction :

| Métrique | Type | Exemple |
|----------|------|---------|
| `duration_seconds` | Temps total | 142.5 s |
| `api_calls.total` | Nombre d'appels API | 20 |
| `api_calls.successful` | Appels réussis | 19 |
| `api_calls.failed` | Appels échoués | 1 |
| `api_calls.success_rate` | Taux de succès | 95 % |
| `records.fetched` | Enregistrements récupérés | 1000 |
| `records.saved` | Enregistrements sauvegardés | 950 |
| `records.duplicates_removed` | Doublons éliminés | 50 |
| `errors` | Liste des erreurs (max 10) | [...] |

#### Timer Decorator

```python
@timer("api_call")
def fetch_offers():
    ...
```

#### ApiCallMetrics (par appel)

| Champ | Description |
|-------|-------------|
| `endpoint` | URL de l'API appelée |
| `duration_ms` | Temps de réponse |
| `status_code` | Code HTTP |
| `success` | Succès/échec |
| `records_count` | Enregistrements retournés |
| `retry_count` | Nombre de tentatives |

### 6.3 Health Checks

**Module** : `01_shared/shared/health.py`

Framework de health checks pour les composants GCP :

| Check | Classe | Composant vérifié |
|-------|--------|-------------------|
| API HTTP | `ApiHealthCheck` | Disponibilité d'une API externe |
| GCS | `GcsHealthCheck` | Connectivité + accès bucket |
| BigQuery | `BigQueryHealthCheck` | Connectivité + requête test |
| Secret Manager | `SecretManagerHealthCheck` | Connectivité + listing |

Utilisation :
```python
registry = create_default_health_checks(
    project_id="data-market-386959",
    gcs_bucket="data-market-386959-data-lake-dev"
)
status = registry.run_all()
# {
#   "status": "healthy",
#   "summary": {"total": 3, "healthy": 3, "degraded": 0, "unhealthy": 0},
#   "checks": [...]
# }
```

### 6.4 Cloud Monitoring (GCP)

Provisionné par le module `pipeline_monitoring` en OpenTofu.

#### Uptime Check

| Cible | Chemin | Fréquence | Timeout |
|-------|--------|-----------|---------|
| n8n-dev | `/health` | 60s | 10s |

#### Log-based Metrics (4 métriques custom)

| Nom | Filtre | Type |
|-----|--------|------|
| `cloud_run_job_errors_{env}` | `resource.type="cloud_run_job" severity=ERROR` | DELTA |
| `workflow_errors_{env}` | `resource.type="workflows.googleapis.com/Workflow" severity=ERROR` | DELTA |
| `cloud_run_job_all_{env}` | `resource.type="cloud_run_job"` | DELTA |
| `n8n_errors_{env}` | `resource.type="cloud_run_revision" service_name="n8n-{env}" severity=ERROR` | DELTA |

#### Alert Policies (4 alertes)

| Nom | Condition | Fenêtre | Notification |
|-----|-----------|---------|--------------|
| Extracteur Cloud Run en échec | `cloud_run_job_errors > 0` | 5 min | Email |
| Chargement BigQuery en échec | `workflow_errors > 0` | 5 min | Email |
| Erreurs n8n | `n8n_errors > 0` | 5 min | Email |
| Pipeline inactif 24h | `cloud_run_job_all = 0` | 24h | Email |

#### Dashboard Monitoring

Widgets du dashboard `pipeline_overview` :
- Statut n8n (uptime check, moyenne 3600s)
- Graphiques d'erreurs par service
- Volumes d'exécution Cloud Run Jobs

---

## 7. KPI & Métriques

### 7.1 KPIs Métier (Dashboard Looker Studio)

Ces KPIs sont calculés par les modèles dbt marts :

| KPI | Table source | Formule | Usage |
|-----|-------------|---------|-------|
| **Nombre total d'offres Data** | `mart_offres_data_jobs` | `COUNT(offer_id)` | Volume du marché |
| **Répartition géographique** | `mart_recrutement_geographique` | `total_offres BY region/dept` | Carte des recrutements |
| **Top recruteurs** | `mart_recruteurs` | `total_offres BY employer_name` | Classement employeurs |
| **Salaire moyen par poste** | `mart_salaires` | `AVG(salary_min + salary_max)/2` | Benchmark salarial |
| **Part de CDI** | `mart_recrutement_geographique` | `pct_cdi` | Stabilité du marché |
| **Profil corporate employeurs** | `mart_employeurs_corporate` | SIREN, CA, effectif, RSE | Qui recrute ? |
| **Taux d'enrichissement** | `int_adzuna_enrichissement` | `COUNT(siren)/COUNT(*)` | Complétude données |
| **Évolution temporelle** | `mart_offres_data_jobs` | `COUNT BY month` | Tendances du marché |

### 7.2 KPIs Techniques (Monitoring)

| KPI | Source | Seuil d'alerte |
|-----|--------|----------------|
| **Taux de succès des extracteurs** | Cloud Monitoring | < 100 % d'erreurs sur 5 min |
| **Taux de succès des loads BQ** | Cloud Monitoring | < 100 % d'erreurs sur 5 min |
| **Disponibilité n8n** | Uptime Check | < 100 % sur 60s |
| **Staleness du pipeline** | Cloud Monitoring | Aucun run en 24h |
| **Temps d'exécution total** | Logs Cloud Run | > seuil configurable |
| **Volume de données ingérées** | Logs + BQ | Tendance jour/J-1 |
| **Taux d'erreur API** | MetricsCollector | > 5 % d'échecs |

### 7.3 KPIs FinOps

| KPI | Source | Objectif |
|-----|--------|----------|
| **Coût mensuel total** | Billing Export | < 50 €/mois |
| **Coût par exécution** | Billing Export | < 0,05 € |
| **Coût par service** | Billing Export | BigQuery = principal poste |
| **Évolution mensuelle** | Billing Export | Tendance à la baisse |
| **Budget vs réel** | Budget alerts | < 80 % du budget |

---

## 8. Infrastructure as Code (IaC)

### 8.1 OpenTofu — Structure

```
00_infra/opentofu/
├── modules/                          # 14 modules réutilisables
│   ├── gcs_bucket/
│   ├── bigquery_dataset/
│   ├── bigquery_table/
│   ├── cloud_run_job/
│   ├── cloud_run_service/
│   ├── cloud_scheduler_job/
│   ├── workflow/
│   ├── service_account/
│   ├── artifact_registry/
│   ├── secret_manager_secret/
│   ├── pipeline_iam/
│   ├── dbt_iam/
│   ├── scheduler_iam/
│   ├── workload_identity_federation/
│   ├── project_services/
│   └── pipeline_monitoring/
│       ├── main.tf                   # Alert policies + dashboard
│       ├── variables.tf
│       ├── output.tf
│       └── dashboards/
│           └── pipeline_overview.json.tftpl
│
└── environments/
    ├── dev/
    │   ├── main.tf                   # 793 lignes — toutes les ressources
    │   ├── providers.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   ├── backend.tf
    │   ├── terraform.tfvars
    │   ├── workflows/                # 7 templates YAML
    │   └── schemas/                  # 10 fichiers .bqschema
    └── prod/
        └── (même structure)
```

### 8.2 Ressources Provisionnées (dev)

| Catégorie | Ressources | Quantité |
|-----------|-----------|----------|
| **GCS** | Bucket data-lake avec versioning | 1 |
| **BigQuery** | Datasets (staging, intermediate, marts, finops) | 4 |
| **BigQuery** | Tables (offres FT, Adzuna, régions, départements, communes, epcis, sirene, api_entreprise, n8n_societe, tracking) | 10+ |
| **Cloud Run Jobs** | extract-ft, extract-geo, extract-adzuna, api-entreprise, n8n-trigger, dbt-run | 6 |
| **Cloud Run Service** | n8n-dev (port 5678, 1 CPU, 2Gi) | 1 |
| **GCP Workflows** | 6 load workflows + 1 pipeline global | 7 |
| **Cloud Scheduler** | FT 6h, GEO lundi 5h, Adzuna 7h | 3 |
| **Secret Manager** | FT_CLIENT_ID, FT_CLIENT_KEY, ADZUNA_API_ID, ADZUNA_API_KEY, DBT_ENV_SECRET, n8n-encryption-key | 6 |
| **Service Accounts** | pipeline-runner, dbt-runner, n8n-runner, github-ci-cd | 4 |
| **WIF** | Pool + Provider GitHub OIDC | 1 |
| **IAM** | Bindings least-privilege pour chaque SA | ~20 |
| **Monitoring** | Uptime check, 4 log metrics, 4 alert policies, dashboard | 1 module |

### 8.3 Pipeline Global Workflow

Le workflow `pipeline-global-dev` orchestre l'ensemble :

```yaml
Étapes parallèles :
├── run_extract_ft      (Cloud Run Job)
├── run_extract_geo     (Cloud Run Job)
├── run_extract_adzuna  (Cloud Run Job)
├── run_api_entreprise  (Cloud Run Job)
├── run_n8n_extract     (Cloud Run Job)  ← après dbt

Étapes séquentielles (après extract) :
├── load_staging_ft     (Workflow)
├── load_staging_geo    (Workflow)
├── load_staging_adzuna (Workflow)
├── load_staging_api    (Workflow)
├── load_staging_n8n    (Workflow)

Étape finale :
├── run_dbt             (Cloud Run Job)
```

---

## 9. Data Catalog

### 9.1 Tables Staging (Bronze)

| Table | Source | Colonnes | Clé primaire | Volume | Fraîcheur |
|-------|--------|----------|-------------|--------|-----------|
| `staging_offres_ft` | API France Travail | ~50 (payload brut) | `id` | ~500k lignes | Quotidienne |
| `staging_offres_adzuna` | API Adzuna | ~25 | `id` | ~150k lignes | Quotidienne |
| `staging_regions` | geo.api.gouv.fr | code, nom | `code` | 18 lignes | Statique |
| `staging_departements` | geo.api.gouv.fr | code, nom, region | `code` | 101 lignes | Statique |
| `staging_communes` | geo.api.gouv.fr | code, nom, codes postaux, centre, population | `code` | ~35k lignes | Statique |
| `staging_epcis` | geo.api.gouv.fr | code, nom, communes | `code` | ~1k lignes | Statique |
| `staging_sirene` | INSEE (STUB) | — | — | 0 (stub) | — |
| `staging_api_entreprise` | recherche-entreprises.api.gouv.fr | SIREN, finances, dirigeants, egapro, ESS | `(employer_name, nom_commune)` | Variable | Post-extract |
| `staging_n8n_societe` | societe.com (via n8n) | 33 colonnes (JSON-LD + dt/dd + ADSTACK) | `(employer_name, nom_commune)` | Variable | Post-extract |
| `staging_societe_tracking` | — | `employer_name`, `nom_commune`, `processed_at` | `(employer_name, nom_commune)` | Traçage | Temps réel |

### 9.2 Tables Intermédiaires (Silver)

| Table | Description | Lignage |
|-------|-------------|---------|
| `int_geo_communes` | Référentiel géographique consolidé (commune + code postal + département + région + EPCI) | staging_communes → staging_departements → staging_regions → staging_epcis |
| `int_ft_employer_names` | Enrichissement des noms d'employeurs FT (lookup + regex) | staging_offres_ft |
| `int_ft_offres` | Offres FT filtrées Data, dédupliquées, enrichies géo | staging_offres_ft + int_geo_communes + int_ft_employer_names |
| `int_adzuna_offres` | Offres Adzuna filtrées Data, dédupliquées, géo-résolues (3 niveaux) | staging_offres_adzuna + int_geo_communes |
| `int_adzuna_enrichissement` | Enrichissement corporate via API Entreprise + n8n | int_adzuna_offres + staging_api_entreprise + staging_n8n_societe |

### 9.3 Tables Marts (Gold)

| Table | Description | Usage BI |
|-------|-------------|----------|
| `mart_offres_data_jobs` | Table de faits : toutes les offres Data (FT + Adzuna) enrichies | Analyse principale |
| `mart_recrutement_geographique` | Aggrégation géographique (offres, employeurs, CDI, salaires par région/dept/commune) | Carte de chaleur |
| `mart_recruteurs` | Aggrégation par employeur (volume, salaires) | Top recruteurs |
| `mart_employeurs_corporate` | Fiches corporate des recruteurs (SIREN, CA, effectif, RSE) | Profil entreprise |
| `mart_salaires` | Analyse salariale par poste + employeur + localisation | Benchmark salaires |
| `mart_finops_costs` | Coûts GCP quotidiens par service (BigQuery, Cloud Run, GCS...) | Dashboard FinOps |

### 9.4 Tags de Sensibilité

| Tag | Tables concernées |
|-----|-------------------|
| `SENSITIVE_PII` | `staging_offres_ft` (champs contact employeur) |
| `GEOLOCATION` | `staging_offres_ft`, `staging_offres_adzuna` |
| `PUBLIC` | `staging_regions`, `staging_departements`, `staging_communes`, `staging_epcis`, `staging_sirene`, `staging_api_entreprise` |

---

## 10. Extracteurs — Détail par Source

### 10.1 France Travail (`02_extract/france_travail/`)

**Authentification** : OAuth2 client credentials
- `get_token()` : POST vers `/partenaire/oauth2/access_token`
- Cache du token avec `create_authenticated_session()`
- Refresh automatique

**Extraction offres** :
- Pagination (max 150 offres/page), boucle jusqu'à `emptyResults: true`
- Paramètres de recherche : codes ROME Data (M1805, M1806, etc.), 101 départements
- Filtres : min/max age, mots-clés ("data engineer", "data scientist", etc.)
- Déduplication par `id` dans un dict `offers_by_id`

**Extraction référentiels** (7 endpoints) :
- `metiers`, `domaines`, `secteursActivites`, `typesContrats`, `natureContrats`, `dureesTravail`, `employeurTypes`

**Format de sortie** : NDJSON dans `raw/ft/offers/{date}.ndjson`

### 10.2 Géo (`02_extract/geo/`)

**Authentification** : Aucune (API publique)

**Extraction** (4 endpoints) :
- `regions?format=json`
- `departements?format=json`
- `communes?format=json&fields=nom,code,codesPostaux,centre,population,departement,region`
- `epcis?format=json&fields=nom,code,communes`

**Post-traitement** : Extraction des coordonnées depuis le champ `centre` (GeoJSON → lat/lon)

**Format de sortie** : NDJSON dans `raw/geo/{resource}/{date}.ndjson`

### 10.3 Adzuna (`02_extract/adzuna/`)

**Authentification** : App ID + API Key (dans URL)

**Extraction** :
- Pagination par page (max 50 offres/page, 20 pages max)
- Paramètres : catégorie "data-java" ou keywords Data, pays "fr"
- Déduplication par `id`

**Modes** :
- `prod` : extraction complète
- `test` : extraction limitée

**Format de sortie** : NDJSON dans `raw/adzuna/offers/{date}.ndjson`

### 10.4 API Entreprise (`02_extract/api_entreprise/`)

**Dépendance** : nécessite que `int_adzuna_offres` soit peuplée (dbt en amont)

**Processus** :
1. `main.py` : Query BQ → `SELECT DISTINCT employer_name, nom_commune FROM int_adzuna_offres`
2. Pour chaque couple (employeur, commune) : appel à `search_by_name_city()` via `recherche-entreprises.api.gouv.fr`
3. Flattening des résultats : SIREN, SIRET, finances (CA, résultat net), dirigeants, egapro, ESS, association, société à mission
4. Sauvegarde NDJSON + tracking (offres déjà traitées)

**Rate limiting** : 0.15s minimum entre chaque appel (respect quotas État)

**Format de sortie** : NDJSON dans `raw/api_entreprise/{date}.ndjson`

### 10.5 n8n Trigger (`02_extract/n8n_trigger/`)

cf. [Section 13 — n8n & Scraping](#13-n8n--scraping-societecom)

### 10.6 Sirene (`02_extract/sirene/`)

**État** : **STUB** — `print("Hello from sirene!")`

Prévu pour :
- Ingestion des fichiers Parquet SIRENE (INSEE) depuis data.gouv.fr
- Matching SIREN/SIRET avec les noms d'employeurs
- Enrichissement des offres

---

## 11. Transformations dbt — Medallion

### 11.1 Architecture des Modèles

```
03_transform/dbt/
├── dbt_project.yml
├── profiles.yml                     # local (SQLite) / dev / prod / ci (BigQuery)
├── models/
│   ├── sources.yml                  # 6 source groups → BigQuery
│   ├── intermediate_dev/
│   │   ├── int_geo_communes.sql
│   │   ├── int_ft_employer_names.sql
│   │   ├── int_ft_offres.sql
│   │   ├── int_adzuna_offres.sql
│   │   └── int_adzuna_enrichissement.sql
│   └── marts/
│       ├── mart_offres_data_jobs.sql
│       ├── mart_recrutement_geographique.sql
│       ├── mart_recruteurs.sql
│       ├── mart_employeurs_corporate.sql
│       ├── mart_salaires.sql
│       └── mart_finops_costs.sql
├── tests/                           # 7 tests SQL
│   ├── test_marts_not_empty.sql
│   ├── test_offres_have_departments.sql
│   ├── test_employer_names_not_empty.sql
│   ├── test_enriched_offres_have_siren.sql
│   └── test_salary_range_coherence.sql
└── macros/
    └── generate_schema_name.sql     # Custom schema pour CI (ci_pr_{number}_intermediate_dev)
```

### 11.2 Matérialisations

| Dataset | Type | Modèles |
|---------|------|---------|
| `staging_*` | Externe (BQ Load Jobs) | Tables brutes |
| `intermediate_dev` | Table | `int_*` |
| `marts_dev` | Table | `mart_*` |

### 11.3 Logique Métier Clé

#### Filtrage Data (int_ft_offres / int_adzuna_offres)

```sql
-- France Travail : filtre sur codes ROME Data
WHERE r.rome_code IN ('M1805', 'M1806', ...)
   OR lower(job_title) LIKE '%data%'

-- Adzuna : filtre sur titre
WHERE lower(title) LIKE '%data%'
   OR lower(title) LIKE '%datascientist%'
```

#### Résolution Géographique Adzuna (3 niveaux)

1. **Match primaire** : `UPPER(city_name) = commune_nom_upper`
2. **Fallback textuel** : recherche de commune/département/région dans `location_display_name`
3. **Fallback coordonnées** : distance euclidienne minimale entre (lat, lon) offre et moyenne des coordonnées communes

#### Déduplication

```sql
ROW_NUMBER() OVER (PARTITION BY offer_id ORDER BY created_at DESC) = 1
```

#### Enrichissement Noms Employeurs (int_ft_employer_names)

- **Lookup** : dictionnaire de correspondances (noms connus)
- **Regex** : patterns "Rejoindre X", "Groupe X", "Au sein de X"
- **Fallback** : nom brut si aucun enrichissement

### 11.4 Tests dbt (7 tests)

| Test | Type | Vérification |
|------|------|-------------|
| `not_null` | Générique | `offer_id` dans les marts |
| `unique` | Générique | `offer_id` dans `mart_offres_data_jobs` |
| `not_null` | Générique | `nom_departement` dans `mart_recrutement_geographique` |
| `not_null` | Générique | `employer_name` dans `mart_recruteurs` |
| `not_null` | Générique | `siren` dans `mart_employeurs_corporate` |
| Custom SQL | Personnalisé | `salary_min <= salary_max` |
| Custom SQL | Personnalisé | `total_offres > 0` dans les marts |

### 11.5 Support Multi-Dialecte

- **BigQuery** : `UNNEST()` pour les tableaux, `STRUCT` pour les nested fields
- **SQLite** (local) : requêtes simplifiées, pas de nested fields
- **CI** : datasets éphémères avec schema naming `ci_pr_{number}`

---

## 12. Coûts & FinOps

### 12.1 Architecture Serverless — Coût Fixe à 0 €

Tous les composants de calcul sont **serverless scale-to-zero** :

| Service | Coût fixe | Coût variable |
|---------|-----------|---------------|
| Cloud Run Jobs | 0 € (min_instances=0) | Pay-per-use (CPU/mémoire au ms) |
| Cloud Run Service (n8n) | ~30-40 €/mois (1 instance manuelle) | N/A (fixe) |
| BigQuery | 0 € (stockage seulement) | Pay-per-query (€/TB scanné) |
| GCS | ~5 €/mois (stockage data lake) | Pay-per-GB |
| Cloud Workflows | 0 € (palier gratuit 5000 étapes) | Au-delà du gratuit |
| Cloud Scheduler | 0 € (3 jobs gratuits) | N/A |

**Coût estimé par exécution complète du pipeline** : < 0,05 €

### 12.2 Stratégie d'Optimisation

#### BigQuery
- **Partitionnement** : tables partitionnées par date de traitement
- **Clustering** : sur colonnes fréquemment filtrées (employer_name, region)
- **Développement local** : SQLite pour les tests (0 €)
- **Expiration** : données brutes configurables (90 jours max)

#### Cloud Run
- **Scale-to-zero** : pas de coût en veille
- **Ressources ajustées** : 512 MiB, 1 vCPU (suffisant pour Python léger)

#### GCS
- **Lifecycle policies** :
  - 30 jours → Nearline
  - 90 jours → Coldline/Archive
  - Fichiers temporaires → suppression à 7 jours

### 12.3 Dashboard FinOps

Connecté via Looker Studio au dataset `finops_dev` (vue SQL sur l'export billing GCP).

**KPIs FinOps** :
1. Coût total mensuel (net, après crédits)
2. Coût par service (BigQuery, Cloud Run, GCS, Workflows, Scheduler)
3. Tendance journalière
4. Coût moyen par exécution

**Modèle dbt** : `mart_finops_costs` (disponible en BigQuery seulement)

**IAM requis** : `dbt-runner-dev` doit avoir `roles/bigquery.dataViewer` sur le dataset de billing.

---

## 13. n8n & Scraping societe.com

### 13.1 Architecture

```
BigQuery (int_adzuna_offres + staging_api_entreprise)
    │
    ▼
n8n_trigger (Cloud Run Job)
    │  Query BQ : offres avec SIREN non encore scrapées
    │
    ├─(priorité)──> n8n (Cloud Run Service)
    │                    │  Webhook POST /webhook/societe-scraper
    │                    │  Payload: {siren, employer_name, nom_commune}
    │                    ▼
    │               societe.com HTTP GET
    │                    │  URL: https://www.societe.com/societe/{slug}-{siren}.html
    │                    │  slug = lower(cname).replace(/[^a-z0-9]+/g,'-')
    │                    ▼
    │               Response: {siren, employer_name, nom_commune, html}
    │
    └─(fallback)──> scraper.scrape_societe() (direct HTTP)
    │
    ▼
scraper.parse_societe_html(html, siren)
    │  1. JSON-LD (balise <script type="application/ld+json">)
    │     → legalName, SIREN/SIRET/TVA, NAF, date création, adresse, dirigeants
    │  2. dt/dd pairs
    │     → Capital social, Convention collective, Noms commerciaux,
    │        Statut RCS, Statut INSEE, Statut RNE
    │  3. ADSTACK.data (script inline)
    │     → Chiffre d'affaires, Effectif
    ▼
save_ndjson_records() → GCS: raw/n8n_societe/{timestamp}.ndjson
    │
    ▼
BigQuery insert_rows(staging_societe_tracking)
    │  Marque (employer_name, nom_commune) comme traité
    ▼
load-staging-n8n-societe (Workflow)
    │  Charge NDJSON → staging_n8n_societe
    │  Déplace fichiers → raw/n8n_societe/done/
```

### 13.2 Workflow n8n

**Fichier** : `n8n/societe.com-scraper.json`

**Nœuds** :
1. **Webhook** (POST) : reçoit `{siren, employer_name, nom_commune}` → `$json.body.*`
2. **HTTP Request** (GET) : `https://www.societe.com/societe/{slug}-{siren}.html`
3. **Set Output** : transmet siren, employer_name, nom_commune, html
4. **Respond to Webhook** : réponse JSON

**Activation** :
- Importé automatiquement au démarrage du conteneur (n8n import:workflow)
- Désactivé après import → activation via API REST après déploiement
- Script : `n8n/n8n_activate.sh` (owner setup → login → get versionId → activate)

### 13.3 Tables BigQuery

#### staging_n8n_societe (33 colonnes)

| Groupe | Colonnes |
|--------|----------|
| **Identité** | employer_name, nom_commune, siren, siret_siege, tva_intra, legal_name |
| **Classification** | naf_code, naf_label, forme_juridique_code, statut |
| **Dates** | date_creation, scraped_at |
| **Adresse** | adresse_rue, adresse_complement, adresse_code_postal, adresse_ville |
| **Dirigeants** | dirigeants (REPEATED RECORD: nom, prenom, nom_famille, fonction) |
| **Données légales** | capital_social, convention_collective, noms_commerciaux |
| **Statuts** | statut_rcs, statut_insee, statut_rne |
| **Financier** | chiffre_affaires, effectif |

#### staging_societe_tracking (3 colonnes)

| Colonne | Type | Description |
|---------|------|-------------|
| `employer_name` | STRING (REQUIRED) | Nom de l'employeur |
| `nom_commune` | STRING | Commune associée |
| `processed_at` | TIMESTAMP (REQUIRED) | Horodatage du scraping |

### 13.4 Résilience

- **Priority** : n8n webhook en premier
- **Fallback** : HTTP direct si n8n indisponible ou non configuré (`N8N_WEBHOOK_URL`)
- **Rate limiting** : 1 seconde entre chaque requête (évite blocage societe.com)
- **Retries** : jusqu'à 3 tentatives par offre

---

## 14. Environnements

### 14.1 Matrice des Environnements

| Caractéristique | `local` | `dev` | `prod` | `ci` |
|-----------------|---------|-------|--------|------|
| **Type** | Développement | Cloud staging | Production | Pull Request |
| **Data warehouse** | SQLite (fichier) | BigQuery (`staging_dev`) | BigQuery (`staging_prod`) | BigQuery (éphémère) |
| **Stockage** | `02_extract/data/` | GCS data-lake | GCS data-lake | N/A |
| **Secrets** | `.env` | Secret Manager | Secret Manager | WIF GitHub |
| **dbt threads** | 1 | 8 | 8 | 4 |
| **Orchestration** | Manuelle | Cloud Scheduler | Cloud Scheduler | GitHub Actions |
| **Coût** | 0 € | ~50 €/mois | ~TBD | 0 € (éphémère) |

### 14.2 Commutation d'Environnement

```bash
# Variable principale
export STORAGE=local     # vs gcs
export DBT_TARGET_ENV=local  # vs dev / prod / ci
```

### 14.3 CI (environnement éphémère)

- Dataset créé : `ci_pr_{number}` + `ci_pr_{number}_intermediate_dev`
- Suppression garantie : `if: always()` dans le workflow
- Isolation totale : pas d'impact sur les données de dev/prod

### 14.4 Prod vs Dev

- **Prod** : mêmes ressources mais dataset `staging_prod` + scheduler prod
- **n8n** : PAS déployé en prod (le promote tag les images mais Terraform prod n'inclut pas n8n)
- **SIRENE** : stub dans tous les environnements pour l'instant

---

## 15. Gouvernance des Données

### 15.1 Quality Gates

| Étape | Ce qui est vérifié | Comment |
|-------|--------------------|---------|
| **Extraction** | IDs non nuls, dédoublonnage | Code Python (dictionnaire offers_by_id) |
| **Load** | Schéma explicite (autodetect=false) | Workflows BQ Load avec .bqschema |
| **dbt staging → intermediate** | Déduplication (ROW_NUMBER), filtres | SQL dans les modèles |
| **dbt intermediate → marts** | Tests not_null, unique, custom | dbt test (7 tests) |
| **CI** | Lint, format, parse, test, exécution complète | GitHub Actions |

### 15.2 Documentation du Lignage

- **dbt docs** : généré par `dbt docs generate`, visualisation du graphe de dépendances
- **DATA_CATALOG.md** : catalogue manuel avec descriptions, tags, propriétaires
- **Ce document** : vue exhaustive du lignage table par table

### 15.3 Data Ownership

| Dataset | Propriétaire | Consommateur |
|---------|-------------|--------------|
| `staging_offres_ft` | Équipe Data | `int_ft_offres`, `int_ft_employer_names` |
| `staging_offres_adzuna` | Équipe Data | `int_adzuna_offres` |
| `staging_*_geo` | Équipe Data | `int_geo_communes` |
| `staging_api_entreprise` | Équipe Data | `int_adzuna_enrichissement` |
| `staging_n8n_societe` | Équipe Data | `int_adzuna_enrichissement` |
| `int_*` | Équipe Data | `mart_*` |
| `mart_*` | Équipe Data | Dashboard Looker Studio |

### 15.4 SLA

| Métrique | Objectif |
|----------|----------|
| Fraîcheur des données | H-24 (données de la veille disponibles le matin) |
| Disponibilité du pipeline | > 99 % (serverless GCP) |
| Complétude France Travail | 100 % des offres Data publiées |
| Complétude Adzuna | 100 % des offres Data publiées |
| Taux d'enrichissement géographique FT | > 99 % (clé INSEE directe) |
| Taux d'enrichissement géographique Adzuna | > 85 % (3 niveaux de fallback) |
| Taux d'enrichissement corporate | > 70 % des offres Adzuna avec SIREN |

---

## 16. Annexes

### 16.1 Structure Complète du Projet

```
data_market_pipeline/
├── 00_infra/
│   ├── opentofu/
│   │   ├── modules/          (14 modules réutilisables)
│   │   └── environments/
│   │       ├── dev/           (main.tf, providers, variables, schemas, workflows)
│   │       └── prod/
│   └── src/                   (minimal/empty)
├── 01_shared/
│   └── shared/
│       ├── __init__.py
│       ├── storage.py         (abstraction GCS/local)
│       ├── gcs.py             (bas niveau GCS)
│       ├── bigquery.py        (client BQ)
│       ├── secrets.py         (Secret Manager)
│       ├── logging_config.py  (logging standard + structuré)
│       ├── metrics.py         (MetricsCollector, timer)
│       ├── health.py          (HealthCheck framework)
│       ├── n8n.py             (N8nClient)
│       └── recherche_entreprises.py  (company search API)
├── 02_extract/
│   ├── france_travail/        (auth, config, scraper, main)
│   ├── geo/                   (config, scraper, main)
│   ├── adzuna/                (config, scraper, main, README)
│   ├── api_entreprise/        (api, main, Dockerfile)
│   ├── n8n_trigger/           (scraper, main, Dockerfile)
│   └── sirene/                (main stub, Dockerfile)
├── 03_transform/
│   ├── dbt/
│   │   ├── dbt_project.yml
│   │   ├── profiles.yml
│   │   ├── models/
│   │   │   ├── sources.yml
│   │   │   ├── intermediate_dev/  (5 modèles)
│   │   │   └── marts/             (6 modèles)
│   │   ├── tests/                  (7 tests)
│   │   └── macros/
│   │       └── generate_schema_name.sql
│   └── src/ (empty)
├── n8n/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── n8n_activate.sh
│   ├── activate-workflow.js
│   ├── societe.com-scraper.json
│   ├── bucket/
│   │   ├── README.md
│   │   └── input.json.example
│   └── annuaire-entreprises.data.gouv.fr-export-sirene/
├── tests/                     (tests pytest)
├── .github/workflows/
│   ├── ci.yml                 (lint + test + dbt parse)
│   ├── dbt-ci.yml             (dbt run + test sur BQ éphémère)
│   └── release.yml            (build + push + deploy)
├── pyproject.toml              (workspace racine)
├── uv.lock
├── .pre-commit-config.yaml
├── .sqlfluff
├── .python-version
├── AGENTS.md
├── ARCHITECTURE.md
├── BRIEF.md
├── COSTS.md
├── DATA_CATALOG.md
├── N8N_ARCHITECTURE.md
├── OPENCODE.md
└── README.md
```

### 16.2 Commandes Essentielles

```bash
# Setup
uv sync --dev

# Lint & verify (ordre)
uv run ruff check .
uv run dbt parse --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt --target local
uv run sqlfluff lint 03_transform/dbt/models --dialect bigquery
uv run pre-commit run --all-files

# Run extractors (local)
FT_EXTRACT_TARGET=offers uv run python 02_extract/france_travail/main.py
uv run python 02_extract/geo/main.py
uv run python 02_extract/adzuna/main.py

# Run dbt (local SQLite)
DBT_TARGET_ENV=local uv run dbt run --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt

# Docker build (depuis racine)
docker build -f 02_extract/france_travail/Dockerfile -t extract-ft:local .
docker build -f 03_transform/Dockerfile -t dbt_transform:local .
docker build -f n8n/Dockerfile -t n8n:local ./n8n

# IaC
cd 00_infra/opentofu/environments/dev && tofu init && tofu plan && tofu apply
```

### 16.3 Stale/Slow Areas (Améliorations Futures)

| Zone | État actuel | Priorité |
|------|-------------|----------|
| `02_extract/sirene/` | Stub | Haute |
| `02_extract/adzuna/scraper_2.py` | Shim redondant | Basse |
| `00_infra/src/` | Package minimal | Basse |
| `03_transform/src/` | Package minimal | Basse |
| Tests Python | pytest basique | Moyenne |
| n8n scale-to-zero | 1 instance fixe (~30-40€/mois) | Moyenne |
| Prod | Provisionné mais pas encore actif | Haute |

---

> **Généré le** : 2026-06-04
> **Dernière mise à jour** : Juin 2026
> **Dépôt** : https://github.com/Jean-ThomasM/data_market_pipeline
