# Rapport de la stack dbt actuelle (`_old/dbt`)

## 1) Perimetre et objectif

La stack dbt actuelle dans `_old/dbt` sert a transformer les tables `raw_*` chargees en SQLite vers une couche **intermediate/silver** exploitable pour l'analyse.

Architecture cible:

- **Bronze (raw)**: ingestion JSON/NDJSON vers SQLite (`_old/data/geo.sqlite`)
- **Silver (dbt)**: nettoyage, typage, deduplication, enrichissement geo


## 2) Configuration dbt

### `dbt_project.yml`

- Projet: `data_market_pipeline_old`
- Dossier des modeles: `models`
- Materialization par defaut pour `intermediate`: `table`

Implication: chaque run reconstruit des tables physiques silver.

### `profiles.yml`

- Adapter: `sqlite`
- Base cible: `_old/data/geo.sqlite`
- Schema: `main`

Implication: tous les modeles dbt sont materialises dans la base `_old/data/geo.sqlite`.


## 3) Sources declarees

Fichier: `models/sources.yml`

### Source `geo`

- `raw_geo_regions`
- `raw_geo_departements`
- `raw_geo_communes`
- `raw_geo_epcis`

### Source `france_travail`

- `raw_ft_offres`

Point positif: les tables sont clairement classees par **origine fonctionnelle**.


## 4) Modeles silver en place

## `int_geo_communes_silver`

Fichier: `models/intermediate/silver/int_geo_communes_silver.sql`

Traitements:

- jointure des communes avec departements/regions/epcis
- `trim(...)` sur les champs texte
- extraction du premier code postal (`json_extract`)
- cast de `population` en entier

Usage: dimension geo enrichie reutilisable dans d'autres modeles.

## `int_ft_offre_geo_silver`

Fichier: `models/intermediate/silver/int_ft_offre_geo_silver.sql`

Traitements:

- normalisation (`trim` + `nullif('', null)`)
- typage:
  - `date_creation`, `date_actualisation` en date
  - `nombre_postes` en integer
  - `alternance`, `accessible_th` en booleen logique (0/1/null)
- deduplication par `offre_id` (priorite a la plus recente actualisation)
- enrichissement geo via jointures sur les tables raw geo
- filtrage des lignes sans `commune_code`

Usage: table silver offres prete pour analytics et futures couches gold.


## 5) Tests dbt et interpretation

Fichier: `models/intermediate/silver/schema.yml`

Tests actifs:

- `int_ft_offre_geo_silver.offre_id`
  - `not_null` (error)
  - `unique` (error)
- `int_ft_offre_geo_silver.intitule`
  - `not_null` (warn)
- `int_ft_offre_geo_silver.commune_code`
  - `not_null` (warn)
- `int_ft_offre_geo_silver.date_creation`
  - `not_null` (warn)
- `int_geo_communes_silver.commune_nom`
  - `not_null` (error)
- `int_geo_communes_silver.departement_code`
  - `not_null` (warn)

Logique qualite:

- **error**: bloque le pipeline (qualite critique)
- **warn**: signale un ecart sans bloquer (qualite surveillee)


## 6) Etat qualite des donnees (run de reference)

Execution de reference:

`uv run dbt build --project-dir _old/dbt --profiles-dir _old/dbt --select path:models/intermediate/silver+ --indirect-selection eager`

Resultat observe:

- `PASS=8`
- `WARN=1`
- `ERROR=0`

Detail warning:

- `not_null_int_geo_communes_silver_departement_code` -> **94 lignes** avec `departement_code` nul.

Interpretation:

- La qualite globale est **bonne** (aucune erreur bloquante).
- Le warning geo est coherent avec certains cas de communes sans rattachement departement standard (ou cas de jointure non resolus).


## 7) Points forts actuels

- separation claire raw -> silver
- source declaration propre par domaine (`geo` / `france_travail`)
- deduplication explicite des offres
- tests critiques sur l'identifiant offre (`not_null` + `unique`)
- pipeline `_old/main.py` aligne sur un select dbt robuste par chemin:
  - `path:models/intermediate/silver+`


## 8) Limites connues et prochaines etapes recommandees

1. Ajouter des tests relationnels (`relationships`) entre `commune_code` et la dimension geo.
2. Ajouter un test metier custom:
   - `date_actualisation >= date_creation` quand les deux valeurs existent.
3. Ajouter des tests de domaine:
   - `alternance in (0,1)`
   - `accessible_th in (0,1)`
4. Documenter les colonnes (descriptions metier) dans `schema.yml` pour faciliter la gouvernance.
5. Preparer une couche **gold** (KPI metier, agregations, marts).


## 9) Conclusion

La stack dbt `_old` est operationnelle et coherentement structuree:

- ingestion raw stable
- silver de nettoyage/enrichissement en place
- qualite couverte par des tests avec severites adaptees

L'etat actuel est satisfaisant pour un usage analytique initial, avec un seul signal qualite non bloquant a suivre sur la geo (`departement_code` manquant).
