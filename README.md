# Data Market Pipeline

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Infrastructure](https://img.shields.io/badge/infra-OpenTofu-orange.svg)](https://opentofu.org/)
[![Database](https://img.shields.io/badge/warehouse-BigQuery-red.svg)](https://cloud.google.com/bigquery)
[![Orchestration](https://img.shields.io/badge/orchestrator-GCP_Workflows-green.svg)](https://cloud.google.com/workflows)
[![Linter & Formatter](https://img.shields.io/badge/lint-ruff-black.svg)](https://github.com/astral-sh/ruff)

Ce projet implémente un pipeline complet d'ingestion et de transformation de données (ELT) serverless visant à répondre à la question métier suivante :

> **Où recrute-t-on des profils Data (en particulier Data Engineers) en France, dans quelles entreprises, et à quels salaires ?**

---

## 1. Liens Utiles du Projet

* **Tableau Kanban de suivi de projet (Public)** : [GitHub Projects — Data Market Pipeline](https://github.com/users/Jean-ThomasM/projects/1)
* **Dashboard BI (Looker Studio)** : [Looker Studio — Data Market Job Market Dashboard](https://lookerstudio.google.com/reporting/data-market-pipeline-public)
* **Dashboard FinOps (Coûts GCP)** : [Looker Studio — Coûts et Optimisation Cloud](https://lookerstudio.google.com/reporting/data-market-pipeline-costs)
* **Auteur** : **Jean-Thomas Miquelot** ([miquelot.jeanthomas@gmail.com](mailto:miquelot.jeanthomas@gmail.com))

---

## 2. Choix Technologiques : Pourquoi GCP ?

Pour ce projet, le choix de **Google Cloud Platform (GCP)** a été retenu pour sa flexibilité, sa scalabilité et son modèle de tarification entièrement serverless :

1. **Serverless pay-as-you-go (Coût minimal)** : Toutes nos briques de calcul (**Cloud Run Jobs**) et d'orchestration (**Workflows**, **Cloud Scheduler**) s'arrêtent complètement en dehors des périodes d'exécution du pipeline quotidien. Le coût fixe de veille est de **0 €**.
2. **BigQuery (Serverless Data Warehouse)** : Capable de traiter des millions de lignes SQL en quelques millisecondes, BigQuery sépare le stockage (très peu cher) du calcul à la requête. Grâce à l'intégration étroite avec dbt, nous pouvons matérialiser nos tables analytiques efficacement.
3. **Services managés & Sécurité intégrée** : L'utilisation de **Secret Manager** élimine le stockage de clés d'API en clair. Le chaînage IAM (Service Accounts) garantit que chaque tâche ne dispose que des privilèges stricts nécessaires (principe du moindre privilège).

---

## 3. Architecture Globale du Pipeline

Le flux de données commence par l'extraction depuis diverses APIs et se termine par la consommation décisionnelle sur Looker Studio :

```mermaid
flowchart TD
    %% Orchestration
    Scheduler[Cloud Scheduler] ➔|Déclenchement quotidien| Workflow[Cloud Workflows]

    %% Ingestion
    subgraph Ingestion [Ingestion & Ingestion (Cloud Run Jobs)]
        job_ft[extract-ft]
        job_geo[extract-geo]
        job_adz[extract-adzuna]
        job_sirene[extract-sirene <br/>⭐ STUB]
    end

    Workflow ➔|Lance les Jobs| Ingestion

    %% External APIs
    API_FT[API France Travail] ➔|Fetch json| job_ft
    API_GEO[API Géo Gouv] ➔|Fetch json| job_geo
    API_ADZ[API Adzuna] ➔|Fetch json| job_adz
    API_SIR[API Sirene Gouv] -.->|Stub| job_sirene

    %% Storage Data Lake
    bucket[GCS Data Lake <br/>gs://data-market-386959-raw-landing/]
    job_ft ➔|Upload NDJSON| bucket
    job_geo ➔|Upload JSON| bucket
    job_adz ➔|Upload NDJSON| bucket

    %% BigQuery Load
    Workflow ➔|Pilote les Load Jobs| BQLoad[BigQuery Load Jobs]
    bucket ➔|Chargement| BQLoad

    %% BigQuery Layers
    subgraph BigQuery [BigQuery Serverless Data Warehouse]
        bq_raw[Dataset: raw_dev]
        bq_int[Dataset: intermediate_dev]
        bq_marts[Dataset: marts_dev]
    end

    BQLoad ➔ bq_raw

    %% Transformation dbt
    job_dbt[transform-dbt <br/>Cloud Run Job]
    Workflow ➔|Lance la transformation| job_dbt
    
    bq_raw ➔|Lecture| job_dbt
    job_dbt ➔|Écriture tables intermediate| bq_int
    job_dbt ➔|Écriture tables marts| bq_marts

    %% Consommation
    Dashboard[Dashboard BI Looker Studio] ➔|Lecture des Marts| bq_marts
```

Détails complets de l'infrastructure dans [ARCHITECTURE.md](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/ARCHITECTURE.md).

---

## 4. Architecture de Données Medallion

Nos tables de données transitent par 3 zones logiques (Medallion) décrites plus en détail dans le [Catalogue de Données (DATA_CATALOG.md)](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/DATA_CATALOG.md) :

1. **Couche Raw (Bronze)** : Les données brutes chargées telles quelles depuis GCS sans altération (tables `staging_*` alimentées par Google Cloud Workflows).
2. **Couche Intermediate (Silver)** : Nettoyage, typage, déduplication temporelle (offres uniques) et enrichissement par croisement géographique (tables `int_*` gérées par dbt).
3. **Couche Marts (Gold)** : Agrégats analytiques fins optimisés pour le dashboard Looker Studio (tables `mart_*` gérées par dbt).

---

## 5. Tableau des Sources Ingestion

| Source de Données | Format Ingestion | Volume Estimé | Fréquence de mise à jour | Contraintes & Particularités |
| :--- | :--- | :--- | :--- | :--- |
| **France Travail** | `NDJSON` | ~15k offres / jour | Quotidienne | Authentification OAuth2 obligatoire, quota de requêtes par seconde. |
| **Adzuna** | `NDJSON` | ~5k offres / jour | Quotidienne | Authentification via App ID & API Key, limitation de requêtes mensuelles. |
| **API GEO Gouv** | `JSON` | Statique / Faible | Annuelle | API publique sans authentification. |
| **API Sirene** | `NDJSON` | En développement (Stub) | Statique | Préparé en stub pour de futures intégrations. |
| **API Entreprise** | `JSON` | À la demande (Enrichissement) | Temps réel | API publique sans clé, rate-limité à 0,15s par appel pour respecter les quotas de l'État. |

---

## 6. Guide de Démarrage Rapide

### A. Déploiement et Exécution en Local

En local, dbt utilise une base SQLite légère pour vous permettre de coder et de tester vos requêtes SQL gratuitement et sans accès à internet.

#### 1. Prérequis
Assurez-vous d'avoir Python 3.13 et l'outil `uv` installés sur votre machine.

#### 2. Installation du workspace
```bash
# Clonez et installez toutes les dépendances locales
uv sync --dev
```

#### 3. Variables d'environnement locales
Créez un fichier `.env` à la racine ou exportez les variables de configuration.
Exemple pour exécuter l'extracteur France Travail localement :
```bash
export STORAGE=local
export FT_CLIENT_ID=votre-client-id
export FT_CLIENT_KEY=votre-client-key
export FT_EXTRACT_TARGET=offers
```

#### 4. Lancer les extracteurs locaux
```bash
# France Travail
FT_EXTRACT_TARGET=offers uv run python 02_extract/france_travail/main.py

# API GEO Gouv
uv run python 02_extract/geo/main.py

# Adzuna
uv run python 02_extract/adzuna/main.py
```
Les fichiers récoltés sont stockés dans le dossier local `02_extract/data/`.

#### 5. Exécuter les transformations locales dbt (SQLite)
```bash
# Sélection de la cible locale (SQLite)
export DBT_TARGET_ENV=local

# Lancement des modèles et des tests
uv run dbt run --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt
uv run dbt test --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt
```

---

### B. Déploiement et Orchestration Cloud (GCP)

#### 1. Déploiement de l'Infrastructure (IaC OpenTofu)
L'infrastructure cloud se déploie depuis le module `00_infra` :
```bash
cd 00_infra/opentofu/environments/dev
tofu init
tofu plan
tofu apply
```

#### 2. Construction et Envoi des Images Docker
Chaque composant applicatif possède un Dockerfile à construire depuis la racine :
```bash
# Exemple pour dbt
docker build -f 03_transform/Dockerfile -t europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/dbt-transform:latest .
docker push europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/dbt-transform:latest
```

---

## 7. Tests et Vérification du Code (CI)

Pour s'assurer de la qualité du code avant chaque commit, exécutez le pipeline de vérification locale dans l'ordre suivant :

```bash
# 1. Vérification du Lint Python (Ruff)
uv run ruff check .

# 2. Validation de la syntaxe dbt et compilation du graphe
uv run dbt parse --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt --target local

# 3. Validation de la syntaxe SQL (SQLFluff BigQuery dialect)
uv run sqlfluff lint 03_transform/dbt/models --dialect bigquery

# 4. Exécution du formateur et des hooks de pre-commit
uv run pre-commit run --all-files
```
