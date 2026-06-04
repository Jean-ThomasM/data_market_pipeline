# Bibliothèque Partagée (`01_shared`)

Ce module contient le code Python transverse et partagé réutilisé par l'ensemble des extracteurs de données du projet **Data Market Pipeline**.

---

## 1. Structure du Module

```text
01_shared/
├── shared/
│   ├── __init__.py            # Point d'entrée de la bibliothèque
│   ├── bigquery.py            # Requêtes et utilitaires pour BigQuery
│   ├── gcs.py                 # Manipulation de fichiers Google Cloud Storage
│   ├── secrets.py             # Accès sécurisé à GCP Secret Manager
│   ├── storage.py             # Abstraction d'écriture double-cible (local / GCS)
│   ├── recherche_entreprises.py # Client pour l'API publique de Recherche Entreprises
│   ├── health.py              # Utilitaires de surveillance et de health checks
│   ├── metrics.py             # Journalisation des performances et statistiques
│   └── logging_config.py      # Configuration centralisée des logs
├── pyproject.toml
└── README.md
```

---

## 2. Fonctionnalités Clés

### A. Abstraction de Stockage (`shared.storage`)
La fonction `save_ndjson_records` permet d'écrire des enregistrements sous format NDJSON vers une cible abstraite contrôlée par la variable d'environnement `STORAGE` :
* **Cible `local`** : Écriture dans le répertoire local `02_extract/data/`.
* **Cible `gcs`** : Écrit dans un bucket Google Cloud Storage spécifié, sous un préfixe donné (ex: `raw/...`).

### B. Client API Recherche d'Entreprises (`shared.recherche_entreprises`)
Client HTTP résilient vers l'API gouvernementale publique `recherche-entreprises.api.gouv.fr`. Il intègre :
* Gestion automatique du **Rate Limit** (limitation à 0.15s minimum entre requêtes).
* Gestion des erreurs HTTP 429 avec détection de l'en-tête `Retry-After`.
* Matching logique intégrant un algorithme de résolution par distance textuelle ou par région/commune pour maximiser les chances de réconciliation.

### C. BigQuery (`shared.bigquery`)
Fournit la fonction `query_to_dicts` qui encapsule l'exécution de requêtes SQL BigQuery vers des dictionnaires Python standard, simplifiant l'extraction d'informations par les extracteurs dépendants (comme `api_entreprise`).

### D. Secret Manager (`shared.secrets`)
Récupération dynamique des clés secrètes à partir de GCP Secret Manager au runtime, évitant de stocker des mots de passe ou des clés d'API en clair dans l'environnement Cloud Run.

### E. Health & Surveillance (`shared.health` et `shared.metrics`)
* Fournit des mécanismes pour logger l'état de santé du script et valider la configuration requise.
* Journalise les mesures et métriques de performance du pipeline (temps d'exécution, volumétrie de données ingérées).

---

## 3. Installation et Utilisation

Ce package est déclaré comme membre du workspace principal.

### Installation en mode développement (depuis la racine) :
```bash
uv sync --dev --package shared
```

### Importation dans un autre module :
```python
from shared.storage import save_ndjson_records
from shared.secrets import get_secret
```
