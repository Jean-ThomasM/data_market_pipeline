# Commandes dbt utiles (`_old/dbt`)

Ce fichier regroupe les commandes dbt les plus utiles pour le projet `_old`.

## 1) Variables d'environnement utiles

### Cible

- `DBT_TARGET=dev` (par defaut)
- `DBT_TARGET=prod`

### Variables prod BigQuery

- `DBT_BQ_PROJECT`
- `DBT_BQ_DATASET`
- `DBT_BQ_KEYFILE_JSON`
- optionnelles: `DBT_BQ_LOCATION`, `DBT_BQ_PRIORITY`, `DBT_THREADS`, `DBT_BQ_TIMEOUT`


## 2) Commandes de base (dev / SQLite)

### Verifier la config dbt

```bash
uv run dbt debug --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

### Parser le projet (validation statique)

```bash
uv run dbt parse --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

### Construire uniquement la silver intermediaire (+ tests associes)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver+ --indirect-selection eager
```

### Construire uniquement la gold marts (+ tests associes)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/marts/gold+ --indirect-selection eager
```

### Construire silver + gold d'un coup (+ tests associes)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager
```

### Executer seulement les modeles (sans tests)

```bash
uv run dbt run --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver
```

### Executer seulement les tests

```bash
uv run dbt test --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver+
```


## 3) Documentation (lignage + dictionnaire)

### Generer les artefacts docs

```bash
uv run dbt docs generate --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

### Servir l'interface docs en local

```bash
uv run dbt docs serve --project-dir _old/dbt --profiles-dir _old/dbt --target dev --port 8081
```

Ouvrir ensuite `http://localhost:8081`.


## 4) Selection de modele utile

### Un seul modele

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select int_ft_offre_geo_silver
```

### Un modele + ses descendants

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select int_ft_offre_geo_silver+
```

### Tout un dossier (silver)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver+
```

### Tout un dossier (gold)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/marts/gold+
```


## 5) Commandes prod (BigQuery)

### Build prod (variables exportees au prealable)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target prod --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager
```

### Example PowerShell (variables session)

```powershell
$env:DBT_TARGET="prod"
$env:DBT_BQ_PROJECT="my-gcp-project"
$env:DBT_BQ_DATASET="analytics"
$env:DBT_BQ_KEYFILE_JSON="{...json service account...}"
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target prod --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager
```


## 6) Utilitaires maintenance

### Nettoyer les artefacts cibles

```bash
uv run dbt clean --project-dir _old/dbt --profiles-dir _old/dbt
```

### Lister les ressources connues par dbt

```bash
uv run dbt ls --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

### Lister uniquement les modeles silver

```bash
uv run dbt ls --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver
```

### Lister uniquement les modeles gold

```bash
uv run dbt ls --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/marts/gold
```


## 7) Commande pipeline complete `_old/main.py`

Le script `uv run .\_old\main.py` enchaine:

1. extraction geo
2. chargement raw geo
3. extraction France Travail
4. chargement raw FT
5. `dbt build` silver intermediaire

Commande:

```bash
uv run .\_old\main.py
```

## 8) One-liner complet (silver + gold + docs)

Commande unique pour:

1. build silver + gold
2. generer la doc
3. servir l'interface docs

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager; uv run dbt docs generate --project-dir _old/dbt --profiles-dir _old/dbt --target dev; uv run dbt docs serve --project-dir _old/dbt --profiles-dir _old/dbt --target dev --port 8081
```
