# Extracteur API GÉO (`02_extract/geo`)

Ce module gère le téléchargement automatique des référentiels géographiques français officiels via l'API GEO publique.

---

## 1. Rôle et Fonctionnalités

L'extracteur interroge l'API GEO gouvernementale (`geo.api.gouv.fr`) :
* **Sans Authentification** : L'API est publique et ne nécessite pas de clé d'accès.
* **Extraction Multi-Niveaux** : Télécharge les communes (avec population, codes postaux, et codes EPCI), les départements, les régions et les EPCI.
* **Sauvegarde** : Les données sont formatées en JSON et enregistrées localement ou dans un bucket GCS selon le paramétrage.

---

## 2. Configuration Requise

Fichier `.env` minimal pour le lancement en local :

```bash
# Cible de stockage (local ou gcs)
STORAGE=local

# Si stockage GCS :
GCP_PROJECT_ID=votre-projet-gcp
GCS_BUCKET_NAME=nom-du-bucket-gcs
```

---

## 3. Lancement Local

### Installation des dépendances (racine) :
```bash
uv sync --dev --package geo
```

### Exécution du script :
```bash
uv run python 02_extract/geo/main.py
```

---

## 4. Intégration Docker

L'image Docker se construit depuis la racine du dépôt :

```bash
# Build de l'image
docker build -f 02_extract/geo/Dockerfile -t extract-geo:local .

# Exécution du conteneur en local
docker run --rm \
  -e STORAGE=local \
  extract-geo:local
```
