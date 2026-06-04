# Infrastructure-as-Code (`00_infra`)

Ce module gère le provisionnement et la gestion de l'infrastructure Google Cloud Platform (GCP) du projet à l'aide d'**OpenTofu** (alternative open-source à Terraform).

---

## 1. Structure du Code IaC

Le code infrastructure est organisé de manière modulaire :

```text
00_infra/
├── opentofu/
│   ├── environments/
│   │   ├── dev/            # Configuration de l'environnement de développement
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── prod/           # Configuration de l'environnement de production
│   └── modules/            # Modules IaC réutilisables
│       ├── bigquery/       # Création des datasets et tables BigQuery
│       ├── cloud_run/      # Déploiement des Cloud Run Jobs (extracteurs, dbt)
│       ├── gcs/            # Provisionnement des Buckets GCS
│       ├── iam/            # Gestion des Rôles et Comptes de Service
│       ├── secret_manager/ # Configuration des Secrets
│       ├── workflows/      # Définition des workflows d'orchestration
│       └── scheduler/      # Déclencheurs temporels (Cloud Scheduler)
├── src/
├── pyproject.toml
└── README.md
```

---

## 2. Ressources GCP Provisionnées

* **Stockage** : Buckets Cloud Storage pour le stockage brut (`raw landing`) et les configurations.
* **Data Warehouse** : Datasets BigQuery séparés par couche Medallion (`raw`, `staging`, `intermediate`, `marts`) et par environnement (`dev`, `prod`).
* **Compute** : Cloud Run Jobs pour exécuter les conteneurs d'extraction et de transformation.
* **Orchestration** : Workflows GCP pour chaîner les tâches d'extraction, de chargement BigQuery et de calcul d'enrichissement dbt.
* **Sécurité & IAM** : Secret Manager pour stocker de façon sécurisée les clés API (France Travail, Adzuna) et attribution fine des rôles IAM aux comptes de service associés à chaque job.

---

## 3. Déploiement de l'Infrastructure

Pour modifier ou appliquer les changements d'infrastructure :

```bash
# Se placer dans le répertoire de l'environnement cible (ex: dev)
cd 00_infra/opentofu/environments/dev

# Initialiser le backend de stockage d'état (OpenTofu state bucket)
tofu init

# Visualiser les changements planifiés
tofu plan

# Appliquer les modifications sur GCP
tofu apply
```
