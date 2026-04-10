# Commandes dbt utiles (`_old/dbt`)

Ce fichier regroupe les commandes dbt les plus utiles pour le projet `_old`, avec:

- ce que fait chaque commande,
- ce que la commande ne fait pas,
- et le resultat attendu.

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

Ce que ca fait:

- verifie la validite de `profiles.yml` et `dbt_project.yml`,
- teste la connexion a la base cible (ici SQLite en dev),
- confirme l'adapter utilise (sqlite / bigquery).

Resultat attendu:

- `All checks passed!`
- si erreur: probleme de chemin, credentials, target ou adapter.

### Parser le projet (validation statique)

```bash
uv run dbt parse --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

Ce que ca fait:

- parse tous les fichiers dbt (`sql`, `yml`, macros),
- construit le graphe de dependances (DAG),
- detecte erreurs de syntaxe/ref/source avant execution.

Ce que ca ne fait pas:

- ne materialise aucune table,
- ne lance aucun test data.

Resultat attendu:

- commande rapide sans ecriture de modeles en base,
- echec immediat si YAML/Jinja/ref invalide.

### Construire uniquement la silver intermediaire (+ tests associes)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver+ --indirect-selection eager
```

Ce que ca fait:

- construit les modeles silver cibles,
- lance les tests associes (schema tests + singular tests selectionnes).

Resultat attendu:

- tables silver recreees dans la base cible,
- resume final du type `PASS=x WARN=y ERROR=z`.

### Construire uniquement la gold marts (+ tests associes)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/marts/gold+ --indirect-selection eager
```

Ce que ca fait:

- construit les marts gold,
- execute les tests lies a ces marts.

Attention:

- si un modele gold depend d'une silver non reconstruite, preferer `+modele_gold` ou construire silver+gold ensemble.

Resultat attendu:

- marts gold disponibles pour la BI / reporting produit.

### Construire silver + gold d'un coup (+ tests associes)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager
```

Ce que ca fait:

- run complet analytique (silver puis gold),
- tests sur les deux couches.

Resultat attendu:

- pipeline analytique complet a jour,
- un seul resume global PASS/WARN/ERROR.

### Executer seulement les modeles (sans tests)

```bash
uv run dbt run --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver
```

Ce que ca fait:

- construit les modeles selectionnes,
- n'execute pas les tests.

Quand l'utiliser:

- iteration rapide developpement SQL.

### Executer seulement les tests

```bash
uv run dbt test --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver+
```

Ce que ca fait:

- lance uniquement les tests dbt,
- utile apres un `dbt run` ou pour audit qualite.

Resultat attendu:

- statut qualite sans rematerialiser les modeles.


## 3) Documentation (lignage + dictionnaire)

### Generer les artefacts docs

```bash
uv run dbt docs generate --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

Ce que ca fait:

- genere `manifest.json` + `catalog.json` + `index.html` dans `target/`,
- alimente lignage + dictionnaire de donnees.

Resultat attendu:

- fichiers docs presents dans `_old/dbt/target`.

### Servir l'interface docs en local

```bash
uv run dbt docs serve --project-dir _old/dbt --profiles-dir _old/dbt --target dev --port 8081
```

Ce que ca fait:

- lance un serveur HTTP local pour visualiser docs dbt.

Pre-requis:

- avoir execute `dbt docs generate` juste avant.

Ouvrir ensuite `http://localhost:8081`.


## 4) Selection de modele utile

### Un seul modele

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select int_ft_offre_geo_silver
```

Ce que ca fait:

- build + test du seul modele cible (sans forcer tous ses parents).

Resultat attendu:

- utile si les dependances amont sont deja a jour.

### Un modele + ses descendants

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select int_ft_offre_geo_silver+
```

Ce que ca fait:

- construit le modele + tout ce qui depend de lui en aval.

Cas typique:

- verifier impact d'un changement silver sur les couches superieures.

### Tout un dossier (silver)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver+
```

Ce que ca fait:

- build global de toute la couche silver.

### Tout un dossier (gold)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/marts/gold+
```

Ce que ca fait:

- build global de la couche gold.


## 5) Commandes prod (BigQuery)

### Build prod (variables exportees au prealable)

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target prod --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager
```

Ce que ca fait:

- execute le meme code dbt mais sur target `prod` BigQuery.

Pre-requis:

- variables `DBT_BQ_*` definies et valides.

Resultat attendu:

- modeles materialises en BigQuery (dataset prod).

### Example PowerShell (variables session)

```powershell
$env:DBT_TARGET="prod"
$env:DBT_BQ_PROJECT="my-gcp-project"
$env:DBT_BQ_DATASET="analytics"
$env:DBT_BQ_KEYFILE_JSON="{...json service account...}"
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target prod --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager
```

Ce que ca fait:

- montre un mode "session shell" pour injecter les variables prod sans `.env`.


## 6) Utilitaires maintenance

### Nettoyer les artefacts cibles

```bash
uv run dbt clean --project-dir _old/dbt --profiles-dir _old/dbt
```

Ce que ca fait:

- supprime les artefacts locaux (`target`, etc.) selon `clean-targets`.

Quand l'utiliser:

- avant un run propre si artefacts incoherents.

### Lister les ressources connues par dbt

```bash
uv run dbt ls --project-dir _old/dbt --profiles-dir _old/dbt --target dev
```

Ce que ca fait:

- liste modeles/tests/sources reconnus par dbt.

Utile pour:

- verifier qu'un nouveau modele est bien pris en compte.

### Lister uniquement les modeles silver

```bash
uv run dbt ls --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/intermediate/silver
```

Resultat attendu:

- liste des modeles dans le dossier silver uniquement.

### Lister uniquement les modeles gold

```bash
uv run dbt ls --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select path:models/marts/gold
```

Resultat attendu:

- liste des marts gold uniquement.


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

Ce que ca fait:

- pipeline E2E extraction + raw load + transformation dbt.

Resultat attendu:

- base `_old/data/geo.sqlite` a jour avec couches dbt configurees.

## 8) One-liner complet (silver + gold + docs)

Commande unique pour:

1. build silver + gold
2. generer la doc
3. servir l'interface docs

```bash
uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --target dev --select "path:models/intermediate/silver+ path:models/marts/gold+" --indirect-selection eager; uv run dbt docs generate --project-dir _old/dbt --profiles-dir _old/dbt --target dev; uv run dbt docs serve --project-dir _old/dbt --profiles-dir _old/dbt --target dev --port 8081
```

Ce que ca fait:

- sequence complete en local: build analytique + generation docs + lancement UI docs.

Note PowerShell:

- `;` enchaine les commandes meme si la precedente echoue.
- pour bloquer sur erreur, lancer les commandes ligne par ligne.
