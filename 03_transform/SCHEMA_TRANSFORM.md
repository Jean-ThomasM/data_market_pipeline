# Schéma des Transformations (dbt Models)

Ce document décrit le fonctionnement et la structure réels de la couche de transformation SQL opérée par **dbt** au sein du répertoire [03_transform/dbt](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt).

---

## 1. Architecture Réelle du Pipeline d'Ingestion & Transformation

Contrairement à un pattern Medallion classique où dbt orchestre le staging de manière isolée, le projet effectue le chargement brut et le renommage initial directement via les **BigQuery Load Jobs** gérés par Google Cloud Workflows. Ces tables chargées servent directement de sources à dbt.

Le flux de modélisation réel dans dbt est structuré comme suit :

```mermaid
flowchart TD
    %% Sources
    subgraph Sources [Sources BigQuery (chargées par Workflows)]
        src_ft[staging_offres_ft]
        src_adzuna[staging_offres_adzuna]
        src_com[staging_communes]
        src_dep[staging_departements]
        src_reg[staging_regions]
        src_epc[staging_epcis]
    end

    %% Intermediate
    subgraph Intermediate [Couche Intermediate dbt]
        int_geo[int_geo_communes]
        int_emp_names[int_ft_employer_names]
        int_ft[int_ft_offres]
        int_adzuna[int_adzuna_offres]
    end

    %% Marts
    subgraph Marts [Couche Marts dbt]
        mart_jobs[mart_offres_data_jobs]
        mart_geo[mart_recrutement_geographique]
        mart_recru[mart_recruteurs]
    end

    %% Flux géo
    src_com --> int_geo
    src_dep --> int_geo
    src_reg --> int_geo
    src_epc --> int_geo

    %% Flux France Travail
    src_ft --> int_ft
    int_geo --> int_ft
    int_emp_names --> int_ft
    src_ft --> int_emp_names

    %% Flux Adzuna
    src_adzuna --> int_adzuna
    int_geo --> int_adzuna

    %% Flux Marts
    int_ft --> mart_jobs
    int_adzuna --> mart_jobs
    mart_jobs --> mart_geo
    mart_jobs --> mart_recru
```

---

## 2. Modèles de la Couche Intermediate (`intermediate_dev`)

La couche Intermediate consolide, filtre et géocode les données brutes.

### [int_geo_communes.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/intermediate_dev/int_geo_communes.sql)
* **Type** : Table
* **Rôle** : Reconstitue le référentiel géographique des communes de France en agrégeant les tables de l'API Géo (`staging_communes`, `staging_departements`, `staging_regions`, `staging_epcis`).
* **Traitement** : Unionise les codes postaux multiples pour chaque commune et résout les hiérarchies géographiques (Commune ➔ EPCI ➔ Département ➔ Région).

### [int_ft_employer_names.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/intermediate_dev/int_ft_employer_names.sql)
* **Type** : Table
* **Rôle** : Enrichit les noms d'employeurs associés aux offres France Travail.
* **Traitement** : Utilise des correspondances de sous-chaînes (`STRPOS`) et des expressions régulières de repli pour nettoyer les appellations anonymes ou génériques (ex: extrait le nom d'entreprise depuis des phrases comme "Rejoindre [Société]").

### [int_ft_offres.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/intermediate_dev/int_ft_offres.sql)
* **Type** : Table (Clé unique : `offer_id`)
* **Rôle** : Consolidation et géocodage des offres France Travail.
* **Traitement** :
  * Filtre les offres sur des mots-clés relatifs à la Data (`DATA`, `DONNÉE`, etc.).
  * Déduplique les offres (garde le record le plus récent via `row_number() over (partition by id order by updated_at desc)`).
  * Joint le référentiel géo sur le code commune INSEE de l'offre (`lieuTravail.commune`).
  * Récupère le nom d'employeur nettoyé depuis `int_ft_employer_names`.

### [int_adzuna_offres.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/intermediate_dev/int_adzuna_offres.sql)
* **Type** : Table (Clé unique : `offer_id`)
* **Rôle** : Consolidation et géocodage des offres issues d'Adzuna.
* **Traitement** :
  * Filtre les offres d'emploi sur la thématique Data.
  * Résout la géographie des offres via un système de recherche par cascade :
    1. Jointure exacte sur le nom de commune.
    2. Fallback par recherche textuelle de noms de villes ou de départements dans le libellé géographique d'Adzuna.
    3. Fallback géospatial par calcul de distance euclidienne minimale sur les coordonnées de latitude/longitude.

---

## 3. Modèles de la Couche Marts (`marts`)

La couche Marts met à disposition les données finales prêtes pour l'analyse BI.

### [mart_offres_data_jobs.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/marts/mart_offres_data_jobs.sql)
* **Type** : Table
* **Rôle** : Modèle de faits central.
* **Traitement** : Unionise les offres nettoyées de France Travail et d'Adzuna. Filtre les offres pour exclure les alternances (`is_alternance = '0'`) et conserve uniquement les lignes ayant une géolocalisation valide.

### [mart_recrutement_geographique.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/marts/mart_recrutement_geographique.sql)
* **Type** : Table
* **Rôle** : Analyse géographique de la dynamique d'embauche.
* **Traitement** : Agrège les offres par région, département et commune pour calculer le nombre d'offres, la part de CDI, le nombre d'employeurs distincts et les salaires moyens proposés.

### [mart_recruteurs.sql](file:///home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/03_transform/dbt/models/marts/mart_recruteurs.sql)
* **Type** : Table
* **Rôle** : Classement et analyse des employeurs recrutant sur les métiers Data.
* **Traitement** : Agrège les offres au niveau de chaque recruteur pour mesurer le volume d'embauche et calculer les salaires min/max moyens affichés.

---

## 4. Documentation Détaillée et Lignage Interactif

Pour générer la documentation interactive HTML complète de dbt (comprenant le lignage interactif et les métadonnées de colonnes) :

```bash
# Se placer à la racine ou dans 03_transform/dbt et lancer :
export DBT_TARGET_ENV=local
uv run dbt docs generate --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt
uv run dbt docs serve --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt
```
Le serveur local démarrera sur [http://localhost:8080](http://localhost:8080) pour explorer le catalogue interactif dbt.
