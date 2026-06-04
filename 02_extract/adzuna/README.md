# Extracteur API Adzuna (`02_extract/adzuna`)

Ce module gère la récupération automatisée des offres d'emploi auprès d'Adzuna pour les profils Data en France.

---

## 1. Rôle et Fonctionnalités

L'extracteur interroge l'API de recherche d'Adzuna :
* **Authentification** : Requiert un identifiant d'API (`ADZUNA_API_ID`) et une clé d'API (`ADZUNA_API_KEY`).
* **Filtres Métier** : Recherche configurée sur des intitulés de postes et des mots-clés de la Data (Data Engineer, Data Analyst, etc.) localisés en France.
* **Écriture Dual-Path** : Écrit les résultats au format NDJSON en local ou dans un bucket GCS.

---

## 2. Configuration Requise

Définissez les variables d'environnement suivantes dans votre fichier `.env` ou dans votre terminal :

```bash
# Cible de stockage (local ou gcs)
STORAGE=local

# Identifiants API Adzuna
ADZUNA_API_ID=votre-api-id
ADZUNA_API_KEY=votre-api-key

# Si stockage GCS :
GCP_PROJECT_ID=votre-projet-gcp
GCS_BUCKET_NAME=nom-du-bucket-gcs
```

---

## 3. Lancement Local

### Installation des dépendances (racine) :
```bash
uv sync --dev --package adzuna
```

### Exécution du script :
```bash
uv run python 02_extract/adzuna/main.py
```

---

## 4. Intégration Docker

L'image Docker se construit depuis la racine du dépôt :

```bash
# Build de l'image
docker build -f 02_extract/adzuna/Dockerfile -t extract-adzuna:local .

# Exécution du conteneur en local
docker run --rm \
  -e STORAGE=local \
  -e ADZUNA_API_ID=votre-api-id \
  -e ADZUNA_API_KEY=votre-api-key \
  extract-adzuna:local
```
