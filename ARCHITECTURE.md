# Architecture ASCII

## Vue d'ensemble

```text
                                      +------------------+
                                      | Cloud Scheduler  |
                                      +--------+---------+
                                               |
                                               v
                                      +------------------+
                                      |    Workflows     |
                                      +---+---+---+---+
                                          |   |   |
                 +------------------------+   |   +------------------------+
                 |                            |                            |
                 v                            v                            v
       +-------------------+        +-------------------+         +-------------------+
       | extract-ft        |        | extract-geo       |         | extract-sirene    |
       | Cloud Run Job     |        | Cloud Run Job     |         | Cloud Run Job     |
       +---------+---------+        +---------+---------+         +---------+---------+
                 |                            |                             |
                 |                            |                             |
                 v                            v                             v
         France Travail API              API GEO                     API Sirene
                 |                            |                             |
                 +-------------+--------------+--------------+--------------+
                               |                             |
                               v                             |
                    +----------------------+                 |
                    |    GCS Data Lake     |<----------------+
                    | raw landing / archive|
                    +------------+-------------+
                                 |
                                 | BigQuery Load Jobs
                                 | pilotes par Workflows
                                 | schema explicite
                                 | autodetect = false
                                 v
                  +---------------------------+
                  |       BigQuery raw        |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  | transform-dbt / SQL job   |
                  | Cloud Run Job             |
                  +------+------+-------------+
                         |      |
                         |      +------------------------------+
                         |                                     |
                         v                                     v
             +----------------------+              +----------------------+
             | BigQuery staging     |              | dbt docs / lineage   |
             +----------+-----------+              +----------------------+
                        |
                        v
             +----------------------+
             | BigQuery intermediate|
             +----------+-----------+
                        |
                        v
             +----------------------+
             | BigQuery marts       |
             +----------+-----------+
                        |
                        v
             +----------------------+
             | Dashboard BI         |
             +----------------------+


      +---------------------------------------------------------------+
      | Secret Manager + IAM / Service Accounts                       |
      | - FT_CLIENT_ID / FT_CLIENT_KEY                                |
      | - SIRENE_API_KEY si necessaire                                |
      | - droits GCS / BigQuery / Cloud Run / Workflows               |
      +---------------------------------------------------------------+
```

## Lecture par etape

### 1. Extraction

```text
France Travail API ---> extract-ft ------+
                                         |
API GEO -------------> extract-geo ----- +--> GCS raw landing
                                         |
API Sirene ----------> extract-sirene ---+
```

Role :

- Python appelle les APIs
- gere auth, retries, pagination
- ecrit des fichiers bruts dans GCS

Formats recommandes :

- France Travail : `NDJSON`
- GEO : `JSON`
- Sirene : `NDJSON`

### 2. Load

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
- matching entreprises Sirene
- tables finales pour le dashboard

### 4. Consommation

```text
BigQuery marts ---> Dashboard BI
                ---> dbt docs / documentation
```

## Architecture Medallion

```text
RAW
  |
  +-- raw_ft_offres_json
  +-- raw_ft_referentiels_*
  +-- raw_geo_regions
  +-- raw_geo_departements
  +-- raw_geo_communes
  +-- raw_geo_epcis
  +-- raw_sirene_search_results
  +-- raw_sirene_matches
  |
  v
STAGING
  |
  +-- stg_ft_offres
  +-- stg_ft_offres_location
  +-- stg_ft_offres_employer
  +-- stg_ft_offres_salary
  +-- stg_geo_regions
  +-- stg_geo_departements
  +-- stg_geo_communes
  +-- stg_geo_epcis
  +-- stg_sirene_matches
  |
  v
INTERMEDIATE
  |
  +-- int_employer_candidates
  +-- int_ft_offres_geo
  +-- int_ft_offres_employers_matched
  +-- int_ft_offres_enriched
  |
  v
MARTS
  |
  +-- mart_offres_data_jobs
  +-- mart_recrutement_geographique
  +-- mart_entreprises_recruteuses
  +-- mart_salaires
  +-- mart_tendances_publication
```

## Repartition des responsabilites

```text
Python
  - extract API
  - auth
  - retry / pagination
  - ecriture GCS
  - eventuel matching Sirene

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
2. Workflows lance extract-ft
3. Workflows lance extract-geo
4. Workflows declenche les load jobs BigQuery pour FT
5. Workflows declenche les load jobs BigQuery pour GEO
6. Workflows lance extract-sirene
7. Workflows declenche les load jobs BigQuery pour Sirene
8. Workflows lance transform-dbt
9. Les marts BigQuery sont alimentes
10. Le dashboard BI lit les marts
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

- `SIRENE_API_KEY`
  Optionnel pour l'instant.
  Usage : futur `extract-sirene` si l'API retenue l'exige.

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
