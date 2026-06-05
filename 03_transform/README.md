# Module de Transformation (`03_transform`)

Ce module orchestre les transformations de données selon la logique Medallion à l'aide de **dbt** (Data Build Tool).

---

## 1. Rôle et Architecture

Le module lit les données d'ingestion brutes (couche Raw/Staging) et produit les tables intermédiaires et les marts d'analyse :
* **Cible `local`** : Travail hors ligne et tests rapides sur une base de données de développement locale **SQLite** (`staging_offres_ft.sqlite`, `main_intermediate_dev.db`, `main_marts_dev.db`).
* **Cible `dev`** : Modélisation et rafraîchissement des tables réelles sur le data warehouse **Google BigQuery** (projet `data-market-386959`).

Le détail des tables créées est disponible dans [SCHEMA_TRANSFORM.md](SCHEMA_TRANSFORM.md).

---

## 2. Commandes Utiles (Lancement Local)

Tous les commandes s'exécutent depuis la racine du dépôt. Définissez d'abord la cible environnementale (défaut : `local`).

```bash
# 1. Sélectionner l'environnement local (SQLite)
export DBT_TARGET_ENV=local

# 2. Installer les paquets dbt (si nécessaire)
uv run dbt deps --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt

# 3. Lancer les transformations dbt
uv run dbt run --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt

# 4. Exécuter les tests de qualité dbt
uv run dbt test --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt

# 5. Valider la syntaxe SQL (Linting)
uv run sqlfluff lint 03_transform/dbt/models --dialect bigquery
```

---

## 3. Déploiement Cloud (Docker)

En production, dbt est encapsulé dans une image Docker et exécuté comme un **Cloud Run Job** :

```bash
# Build de l'image
docker build -f 03_transform/Dockerfile -t dbt-transform:local .

# Exécution locale avec cible BigQuery (nécessite l'authentification GCP active)
docker run --rm \
  -e DBT_TARGET_ENV=dev \
  -v ~/.config/gcloud:/root/.config/gcloud \
  dbt-transform:local
```
