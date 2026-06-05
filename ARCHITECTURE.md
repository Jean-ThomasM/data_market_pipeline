# Architecture du Pipeline de Données

Ce document décrit l'architecture technique globale, l'orchestration et le flux de données du projet **Data Market Pipeline**.

---

## 1. Schéma d'Architecture Général

Le diagramme suivant présente l'infrastructure globale déployée sur **Google Cloud Platform (GCP)** ainsi que les flux de données associés :

```mermaid
flowchart TD
    %% Orchestration
    Scheduler[Cloud Scheduler] ➔|Déclenchement quotidien| Workflow[Cloud Workflows]

    %% Ingestion Parallèle
    subgraph Ingestion [Ingestion & Chargement (Cloud Run & Workflows)]
        job_ft[extract-ft-dev <br/>Cloud Run Job]
        job_geo[extract-geo-dev <br/>Cloud Run Job]
        job_adz[extract-adzuna-dev <br/>Cloud Run Job]
        job_api[api-entreprise-dev <br/>Cloud Run Job]
    end

    Workflow ➔|1. Lance les Jobs en parallèle| Ingestion

    %% External APIs
    API_FT[API France Travail] ➔|OAuth2 Fetch| job_ft
    API_GEO[API Géo Gouv] ➔|Public Fetch| job_geo
    API_ADZ[API Adzuna] ➔|Fetch JSON| job_adz
    API_ENT[API Recherche Entreprises] ➔|Fetch JSON| job_api

    %% GCS Data Lake
    bucket[GCS Data Lake <br/>gs://data-market-386959-data-lake-dev/]
    job_ft ➔|Upload NDJSON| bucket
    job_geo ➔|Upload JSON| bucket
    job_adz ➔|Upload NDJSON| bucket
    job_api ➔|Upload NDJSON| bucket

    %% BigQuery Load
    Workflow ➔|2. Lance les BQ Load Jobs| BQLoad[BigQuery Load Jobs]
    bucket ➔|Chargement brut| BQLoad

    %% BigQuery Layers
    subgraph BigQuery [BigQuery Serverless Data Warehouse]
        bq_raw[Couche Raw / staging_*]
        bq_int[Couche Intermediate / int_*]
        bq_marts[Couche Marts / mart_*]
    end

    BQLoad ➔ bq_raw

    %% Transformation dbt
    job_dbt[dbt-run-dev <br/>Cloud Run Job]
    Workflow ➔|3. Lance les transformations| job_dbt
    
    bq_raw ➔|Lecture| job_dbt
    job_dbt ➔|Nettoyage & Jointures| bq_int
    job_dbt ➔|Agrégations Gold| bq_marts

    %% Scraping societe.com (n8n)
    subgraph n8n_flow [Scraping Complémentaire (n8n)]
        job_n8n_trig[n8n-trigger-dev <br/>Cloud Run Job]
        n8n_proxy[n8n-dev <br/>Cloud Run Service]
        web_societe[Site societe.com]
        load_n8n[load-n8n-workflow <br/>GCP Workflow]
    end

    Workflow ➔|4. Lance le scraping societe.com| job_n8n_trig
    bq_int ➔|Offres non traitées| job_n8n_trig
    
    job_n8n_trig ➔|Appel Webhook| n8n_proxy
    n8n_proxy ➔|Scrape HTML| web_societe
    n8n_proxy ➔|Upload NDJSON scrapé| bucket
    
    Workflow ➔|5. Charge les données scrapées| load_n8n
    bucket ➔|Chargement n8n| load_n8n
    load_n8n ➔|Alimente staging_n8n_societe| bq_raw

    %% Consommation
    Dashboard[Dashboard Looker Studio] ➔|Lecture des Marts| bq_marts
    docs[dbt docs / Lineage HTML] ➔|Généré par dbt| bq_marts
```

---

## 2. Description Étape par Étape

### 2.1 Extraction (Ingestion)

* **extract-ft** (Cloud Run Job) : Interroge l'API France Travail avec authentification OAuth2, gère la pagination et écrit les offres brutes au format NDJSON dans GCS.
* **extract-geo** (Cloud Run Job) : Interroge l'API GEO publique pour récupérer les référentiels géographiques (communes, départements, régions, EPCI) et les écrit au format JSON dans GCS.
Role :
- Python appelle les APIs
- gere auth, retries, pagination
- ecrit des fichiers bruts dans GCS

Formats de fichiers stockés dans GCS :
- France Travail : `NDJSON`
- GEO : `JSON`
- Adzuna : `NDJSON`

## 2. Load

```text
GCS raw landing ---> Workflows ---> BigQuery Load Jobs ---> BigQuery raw
```

Role :

- Workflows retrouve les fichiers a charger
- Workflows cible les bonnes tables BigQuery
- Workflows declenche les BigQuery Load Jobs
- schema explicite fourni
- `autodetect = false`
- aucune transformation metier a cette etape

### 3. Transform

```text
BigQuery raw ---> dbt / SQL ---> staging ---> intermediate ---> marts
```

Role :

- nettoyage
- typage
- jointures
- enrichissement geographique
- tables finales pour le dashboard

### 4. Consommation

```text
BigQuery marts ---> Dashboard BI
                ---> dbt docs / documentation
```

## Architecture Medallion

```text
STAGING (raw)
  |
  +-- staging_offres_ft
  +-- staging_offres_adzuna
  +-- staging_communes
  +-- staging_departements
  +-- staging_regions
  +-- staging_epcis
  +-- staging_api_entreprise
  +-- staging_n8n_societe
  |
  v
INTERMEDIATE (clean & enrich)
  |
  +-- int_geo_communes
  +-- int_ft_employer_names
  +-- int_ft_offres
  +-- int_adzuna_offres
  +-- int_adzuna_enrichissement
  |
  v
MARTS (analytics)
  |
  +-- mart_offres_data_jobs
  +-- mart_recrutement_geographique
  +-- mart_recruteurs
  +-- mart_employeurs_corporate
  +-- mart_salaires
  +-- mart_finops_costs
```

## Repartition des responsabilites

```text
Python
  - extract API
  - auth
  - retry / pagination
  - ecriture GCS
  - matching API Entreprise

SQL / dbt
  - staging
  - intermediate
  - marts
  - tests
  - documentation
  - lineage

IaC
  - GCS
  - BigQuery
  - schemas des tables raw
  - Secret Manager
  - IAM
  - Cloud Run Jobs
  - Workflows
  - Scheduler
```

## Sequence d'execution cible

```text
1. Cloud Scheduler declenche Workflows
2. Workflows lance extract-ft, extract-geo, extract-adzuna, api-entreprise en parallele
3. Workflows declenche les load jobs BigQuery pour chaque source
4. Workflows lance transform-dbt
5. Les marts BigQuery sont alimentes
6. Le dashboard BI lit les marts
```

## Datasets BigQuery cibles

```text
raw_<env>
staging_<env>
intermediate_<env>
marts_<env>
```

## Tableau des variables

### OpenTofu / Terraform

- `project_id`
  Obligatoire. Exemple : `my-gcp-project`
  Usage : creation des ressources GCP.

- `region`
  Obligatoire. Exemple : `europe-west9`
  Usage : Cloud Run, Artifact Registry, orchestration.

- `environment`
  Obligatoire. Exemple : `dev` ou `prod`
  Usage : separation des environnements, nommage des ressources.

- `bucket_location`
  Obligatoire. Exemple : `EU`
  Usage : bucket GCS.

- `bigquery_location`
  Obligatoire. Exemple : `EU`
  Usage : datasets BigQuery.

### Secret Manager

- `FT_CLIENT_ID`
  Obligatoire.
  Usage : authentification France Travail pour `extract-ft`.

- `FT_CLIENT_KEY`
  Obligatoire.
  Usage : authentification France Travail pour `extract-ft`.

### Variables du Cloud Run Job

- `STORAGE`
  Obligatoire pour `extract-ft` et `extract-geo`. Exemple : `gcs`
  Usage : choisit le backend de persistance des extracteurs.


- `GCP_PROJECT_ID`
  Obligatoire. Exemple : `my-gcp-project`
  Usage : lecture des secrets et validation de config.

- `GCS_BUCKET_NAME`
  Obligatoire. Exemple : `my-bucket`
  Usage : lecture des configs metier et ecriture des fichiers raw.

- `FT_EXTRACT_TARGET`
  Obligatoire pour `extract-ft` batch. Exemple : `offers`
  Usage : choisit la cible d'extraction France Travail.

- `FT_SEARCH_PARAMS_OBJECT`
  Recommande. Exemple : `config/search_params_prod.json`
  Usage : chemin de la config de recherche FT dans le bucket.

- `SCOPE_API_FT_EMPLOI`
  Optionnel. Exemple : `api_offresdemploiv2 o2dsoffre`
  Usage : surcharge du scope OAuth France Travail.

### Configuration metier dans GCS

- `config/search_params_prod.json`
  Obligatoire pour FT prod si on utilise la version decoupee.
  Exemple : `gs://bucket/config/search_params_prod.json`
  Usage : parametres de recherche France Travail.

- `config/search_params_prod_no_departement.json`
  Alternative prudente si le filtre `departement` n'est pas valide.
  Exemple : `gs://bucket/config/search_params_prod_no_departement.json`
  Usage : parametres de recherche France Travail sans decoupage departement.

### Parametres Workflows

- `run_id`
  Optionnel mais recommande. Exemple : `2026-04-07T14:00:00Z`
  Usage : tracabilite et correlation des runs.

- `logical_date`
  Optionnel. Exemple : `2026-04-07`
  Usage : partition logique et pilotage du run.

### Regles de repartition

- OpenTofu / Terraform
  Porte les variables d'infrastructure, les definitions des jobs, les references aux secrets et IAM.

- Secret Manager
  Porte uniquement les secrets applicatifs sensibles.

- Variables du Cloud Run Job
  Portent la configuration runtime stable des jobs batch.

- GCS
  Porte la configuration metier versionnable, par exemple `search_params`.

- Workflows
  Porte les parametres dynamiques de run, par exemple `run_id` ou `logical_date`.
