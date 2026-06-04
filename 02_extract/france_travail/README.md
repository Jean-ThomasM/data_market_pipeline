# Extracteur France Travail (`02_extract/france_travail`)

Ce module gère la récupération automatisée des offres d'emploi et des référentiels métiers de France Travail (anciennement Pôle Emploi).

---

## 1. Rôle et Fonctionnalités

L'extracteur interroge l'API des Offres d'emploi v2 de France Travail :
* **Authentification** : Gestion du protocole OAuth2 (Client Credentials Flow) pour obtenir un jeton d'accès temporaire auprès de France Travail.
* **Extraction des Référentiels** : Extraction des référentiels (codes ROME, métiers, géographiques) utiles à la validation.
* **Extraction des Offres** : Récupération des offres d'emploi actives correspondant à nos critères de recherche Data (Data Engineer, Data Analyst, Data Scientist).
* **Écriture Dual-Path** : Sauvegarde locale ou vers Google Cloud Storage selon les variables d'environnement.

---

## 2. Configuration Requise

Pour lancer cet extracteur en local, définissez les variables d'environnement suivantes dans un fichier `.env` ou exportez-les dans votre terminal :

```bash
# Cible de stockage (local ou gcs)
STORAGE=local

# Identifiants API France Travail (à récupérer sur le portail développeur de France Travail)
FT_CLIENT_ID=votre-client-id
FT_CLIENT_KEY=votre-client-key

# Cible d'extraction (offers | referentials | all)
FT_EXTRACT_TARGET=offers

# Si stockage GCS :
GCP_PROJECT_ID=votre-projet-gcp
GCS_BUCKET_NAME=nom-du-bucket-gcs
```

---

## 3. Lancement Local

### Installation des dépendances (racine) :
```bash
uv sync --dev --package france-travail
```

### Exécution du script :
```bash
FT_EXTRACT_TARGET=offers uv run python 02_extract/france_travail/main.py
```

---

## 4. Intégration Docker

L'image Docker se construit depuis la racine du dépôt :

```bash
# Build de l'image
docker build -f 02_extract/france_travail/Dockerfile -t extract-ft:local .

# Exécution du conteneur en local
docker run --rm \
  -e STORAGE=local \
  -e FT_CLIENT_ID=votre-client-id \
  -e FT_CLIENT_KEY=votre-client-key \
  -e FT_EXTRACT_TARGET=offers \
  extract-ft:local
```
