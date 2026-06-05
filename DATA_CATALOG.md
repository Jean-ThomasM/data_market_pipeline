# Catalogue de Données (Data Catalog)

Ce document fournit une description exhaustive des tables de données du projet **Data Market Pipeline** hébergées sur BigQuery (ou SQLite en local), selon le modèle d'architecture Medallion appliqué au projet.

---

## Vue d'ensemble du Lignage (Data Lineage)

Le lignage des données suit un flux d'ingestion et de transformation structuré :

```mermaid
flowchart TD
    %% Ingestion / Raw
    subgraph Ingestion [1. Extraction & Load (Raw/Staging)]
        raw_ft[staging_offres_ft]
        raw_adzuna[staging_offres_adzuna]
        raw_geo_com[staging_communes]
        raw_geo_dep[staging_departements]
        raw_geo_reg[staging_regions]
        raw_geo_epc[staging_epcis]
        raw_api_ent[staging_api_entreprise]
        raw_n8n[staging_n8n_societe]
    end

    %% Intermediate
    subgraph Intermediate [2. Transformation & Enrichissement (Intermediate)]
        int_geo[int_geo_communes]
        int_ft_emp[int_ft_employer_names]
        int_ft_offres[int_ft_offres]
        int_adzuna_offres[int_adzuna_offres]
        int_adzuna_enrich[int_adzuna_enrichissement]
    end

    %% Marts
    subgraph Marts [3. Restitution (Marts)]
        mart_fact[mart_offres_data_jobs]
        mart_geo[mart_recrutement_geographique]
        mart_recruteurs[mart_recruteurs]
        mart_corporate[mart_employeurs_corporate]
        mart_sal[mart_salaires]
    end

    %% Relations de dépendance
    raw_geo_com --> int_geo
    raw_geo_dep --> int_geo
    raw_geo_reg --> int_geo
    raw_geo_epc --> int_geo

    raw_ft --> int_ft_offres
    int_geo --> int_ft_offres
    int_ft_emp --> int_ft_offres
    raw_ft --> int_ft_emp

    raw_adzuna --> int_adzuna_offres
    int_geo --> int_adzuna_offres

    raw_api_ent --> int_adzuna_enrich
    raw_n8n --> int_adzuna_enrich
    int_adzuna_offres --> int_adzuna_enrich

    int_ft_offres --> mart_fact
    int_adzuna_enrich --> mart_fact

    mart_fact --> mart_geo
    mart_fact --> mart_recruteurs
    mart_fact --> mart_sal
    int_adzuna_enrich --> mart_corporate
```

---

## 1. Couche Raw / Staging (Data Lake Ingestion)

Ces tables brutes proviennent directement de l'extraction des APIs externes. Dans ce projet, l'étape de "staging" BigQuery est opérée directement par les **BQ Load Jobs** via l'orchestrateur Google Cloud Workflows.

### Table : `staging_offres_ft`
* **Source** : API France Travail (Offres d'emploi v2)
* **Fréquence de rafraîchissement** : Quotidienne (Batch)
* **Propriétaire / Consommateur** : Équipe Data / `int_ft_offres` & `int_ft_employer_names`
* **Tags de Sensibilité** : 
  * `SENSITIVE_PII` (Données personnelles dans les champs de contact / URL de postulation de l'employeur)
  * `GEOLOCATION` (Coordonnées géographiques et codes géographiques de l'offre d'emploi)
* **Description** : Contient l'intégralité du payload brut des offres d'emploi récupérées de France Travail pour les profils Data en France.

### Table : `staging_offres_adzuna`
* **Source** : API Adzuna (Search API)
* **Fréquence de rafraîchissement** : Quotidienne (Batch)
* **Propriétaire / Consommateur** : Équipe Data / `int_adzuna_offres`
* **Tags de Sensibilité** :
  * `GEOLOCATION` (Coordonnées de l'offre d'emploi, display name géographique de la commune)
* **Description** : Contient l'intégralité des offres d'emploi récoltées auprès d'Adzuna pour les profils Data en France.

### Tables de Référentiel Géo (`staging_communes`, `staging_departements`, `staging_regions`, `staging_epcis`)
* **Source** : API GEO (api.gouv.fr)
* **Fréquence de rafraîchissement** : Statique / Annuelle
* **Propriétaire / Consommateur** : Équipe Data / `int_geo_communes`
* **Tags de Sensibilité** : `PUBLIC` (Aucune donnée sensible)
* **Description** : Référentiels géographiques officiels de la République Française (Codes INSEE, codes postaux, populations, rattachements EPCI/Régions).



---

## 2. Couche Intermediate (Clean & Enrich)

Modèles dbt intermédiaires effectuant le typage, le nettoyage, la déduplication et le croisement géographique.

### Modèle : `int_geo_communes`
* **Clé primaire** : `commune_code` + `code_postal`
* **Lignage source** : `staging_communes` ➔ `staging_departements` ➔ `staging_regions` ➔ `staging_epcis`
* **Description** : Référentiel géographique français consolidé à la maille commune/code postal.
* **Champs majeurs** :
  * `commune_code` : Code INSEE de la commune (ex: `75101`).
  * `code_postal` : Code postal associé.
  * `commune_nom` : Nom de la commune.
  * `departement_code` / `departement_nom` : Rattachement départemental.
  * `region_code` / `region_nom` : Rattachement régional.
  * `epci_code` / `epci_nom` : Rattachement à l'intercommunalité (EPCI).

### Modèle : `int_ft_employer_names`
* **Clé primaire** : `offer_id`
* **Lignage source** : `staging_offres_ft`
* **Description** : Nettoyage et enrichissement des noms d'employeurs France Travail (souvent anonymes ou mal saisis) par recherche textuelle de patterns de fallback (ex: "Rejoindre X", "Groupe Y") ou par lookup dans un dictionnaire d'entreprises.
* **Champs majeurs** :
  * `offer_id` : ID unique de l'offre.
  * `employer_name_raw` : Nom brut.
  * `employer_name_enriched` : Nom nettoyé et enrichi.
  * `enrichment_source` : Méthode ayant fourni l'enrichissement (`raw`, `lookup`, `regex`, `fallback`).

### Modèle : `int_ft_offres`
* **Clé primaire** : `offer_id`
* **Lignage source** : `staging_offres_ft` + `int_geo_communes` + `int_ft_employer_names`
* **Description** : Liste des offres France Travail filtrées sur les métiers de la Data, dédupliquées par ID d'offre et enrichies géographiquement et au niveau employeur.
* **Champs majeurs** :
  * `offer_id` : ID unique.
  * `job_title` / `job_description` : Intitulé et description textuelle du poste.
  * `employer_name` / `employer_description` : Employeur consolidé.
  * `nom_commune` / `numero_departement` / `nom_region` : Localisation issue du référentiel GEO.
  * `has_salary_info` : Flag (`0`/`1`) indiquant si un salaire est mentionné.
  * `is_alternance` : Flag (`0`/`1`) pour l'alternance.

### Modèle : `int_adzuna_offres`
* **Clé primaire** : `offer_id`
* **Lignage source** : `staging_offres_adzuna` + `int_geo_communes`
* **Description** : Liste des offres Adzuna filtrées sur les métiers de la Data, avec une résolution géographique complexe combinant la correspondance exacte de noms, des fallbacks textuels sur l'attribut `location_display_name` et des recherches de distance euclidienne minimale sur coordonnées GPS (latitude/longitude) face au référentiel géographique.
* **Champs majeurs** :
  * `offer_id` : ID unique.
  * `job_title` : Intitulé.
  * `salary_min` / `salary_max` : Fourchette de salaire proposée.
  * `nom_commune` / `numero_departement` / `nom_region` : Localisation géocodée.
  * `has_salary_info` / `is_alternance` : Flags techniques de classification.

### Modèle : `int_adzuna_enrichissement`
* **Clé primaire** : `offer_id`
* **Lignage source** : `int_adzuna_offres` + `staging_api_entreprise` + `staging_n8n_societe`
* **Description** : Enrichissement corporate des offres Adzuna via l'API Recherche Entreprises (SIREN, SIRET, finances, nature juridique, effectif, dirigeants) et le scraping societe.com via n8n (capital social, convention collective, chiffre d'affaires).
* **Champs majeurs** :
  * `offer_id` / `employer_name` / `nom_commune` : Clés de jointure.
  * `siren` / `siret_siege` : Identifiants officiels de l'entreprise.
  * `nom_raison_sociale` : Raison sociale officielle.
  * `nature_juridique` / `categorie_entreprise` : Forme juridique et catégorie (PME/ETI/GE).
  * `ca_dernier_exercice` / `resultat_net_dernier` : Données financières du dernier exercice (k€).
  * `egapro_renseignee` / `est_ess` / `est_societe_mission` : Indicateurs RSE.
  * `capital_social` / `convention_collective` / `effectif_societe` : Données societe.com.

---

## 3. Couche Marts (Restitution BI)

Modèles dbt finaux prêts à être exposés au Dashboard Looker Studio ou autre outil décisionnel.

### Modèle : `mart_offres_data_jobs`
* **Clé primaire** : `offer_id`
* **Lignage source** : `int_ft_offres` + `int_adzuna_offres` + `int_adzuna_enrichissement`
* **Description** : Table de faits consolidée au grain de l'offre d'emploi Data (hors alternance, ayant une géolocalisation valide). Fusionne les flux France Travail et Adzuna. Les offres Adzuna sont enrichies des données corporate (SIREN, finances, catégorie d'entreprise, RSE, capital social).
* **Champs majeurs** :
  * `offer_id` : ID de l'offre.
  * `source_system` : Origine de l'offre (`France Travail` ou `Adzuna`).
  * `job_title` / `job_description` : Titre et description.
  * `contract_type` : Type de contrat (CDI, CDD, etc.).
  * `employer_name` : Nom de l'employeur.
  * `nom_region` / `nom_departement` / `nom_commune` / `code_postal` : Informations de géolocalisation complètes.
  * `salary_min` / `salary_max` : Fourchette de salaire annuel brut (en EUR).
  * `siren` / `siret_siege` : SIREN et SIRET du siège (Adzuna uniquement).
  * `nom_raison_sociale` : Raison sociale officielle.
  * `nature_juridique` / `categorie_entreprise` : Forme juridique et catégorie.
  * `tranche_effectif_salarie` : Tranche d'effectifs INSEE.
  * `egapro_renseignee` / `est_ess` / `est_societe_mission` : Indicateurs RSE.
  * `ca_dernier_exercice` / `resultat_net_dernier` : Données financières (k€).
  * `capital_social` / `convention_collective` : Données légales.

### Modèle : `mart_recrutement_geographique`
* **Clé primaire** : `nom_region` + `nom_departement` + `nom_commune`
* **Lignage source** : `mart_offres_data_jobs`
* **Description** : Vue d'agrégation géographique permettant de cartographier la dynamique de recrutement Data en France.
* **Champs majeurs** :
  * `nom_region` / `nom_departement` / `nom_commune` : Axes d'analyse géographiques.
  * `total_offres` : Nombre d'offres Data publiées.
  * `total_employeurs_distincts` : Nombre d'entreprises différentes qui recrutent.
  * `pct_cdi` : Part d'offres en CDI (en %).
  * `salaire_min_moyen` / `salaire_max_moyen` : Salaires moyens proposés sur le territoire.

### Modèle : `mart_recruteurs`
* **Clé primaire** : `employer_name`
* **Lignage source** : `mart_offres_data_jobs`
* **Description** : Vue d'agrégation employeurs listant les entreprises les plus actives dans le recrutement de profils Data.
* **Champs majeurs** :
  * `employer_name` : Nom de l'entreprise.
  * `total_offres` : Volume total d'offres publiées.
  * `total_offres_avec_salaire` : Volume d'offres indiquant une rémunération.
  * `salaire_min_moyen` / `salaire_max_moyen` : Fourchette de salaires moyens proposés par cet employeur.

### Modèle : `mart_employeurs_corporate`
* **Clé primaire** : `(employer_name, nom_commune)`
* **Lignage source** : `int_adzuna_enrichissement`
* **Description** : Fiches corporate des employeurs Adzuna, dédupliquées par (employeur, commune). Une ligne = une entreprise avec ses données d'identité (SIREN, raison sociale), financières (CA, résultat net), structure (effectif, capital social, convention collective), RSE (egapro, ESS) et recrutement (volume d'offres, salaires moyens).
* **Champs majeurs** :
  * `employer_name` / `nom_commune` : Clé d'identification.
  * `siren` / `siret_siege` / `nom_raison_sociale` : Identité officielle.
  * `nature_juridique` / `categorie_entreprise` : Profil juridique.
  * `tranche_effectif_salarie` / `effectif_societe` : Taille de l'entreprise.
  * `ca_dernier_exercice` / `resultat_net_dernier` : Performance financière.
  * `capital_social` / `convention_collective` : Données légales.
  * `egapro_renseignee` / `est_ess` / `est_association` / `est_societe_mission` : RSE.
  * `total_offres` / `salaire_min_moyen` / `salaire_max_moyen` : Métriques recrutement.

### Modèle : `mart_salaires`
* **Clé primaire** : `(employer_name, nom_commune, job_title)`
* **Lignage source** : `mart_offres_data_jobs`
* **Description** : Analyse des salaires par poste et employeur. Permet de comparer les rémunérations proposées par type de poste et profil d'entreprise.
* **Champs majeurs** :
  * `employer_name` / `nom_commune` / `job_title` : Axes d'analyse.
  * `siren` / `nom_raison_sociale` / `nature_juridique` / `categorie_entreprise` : Profil employeur.
  * `nombre_offres` : Volume d'offres pour ce couple.
  * `salaire_min_moyen` / `salaire_max_moyen` : Salaires moyens.
  * `salaire_min_global` / `salaire_max_global` : Étendue des salaires.

### Modèle : `mart_finops_costs`
* **Dataset** : `finops_dev`
* **Lignage source** : `billing_raw.gcp_billing_export_v1_*` (export facturation GCP)
* **Description** : Coûts GCP quotidiens agrégés par service, ressource et environnement. Permet le pilotage FinOps du pipeline via Looker Studio.
* **Champs majeurs** :
  * `facturation_mois` : Mois de facturation.
  * `date_usage` : Jour de consommation.
  * `service_nom` : Service GCP (BigQuery, Cloud Run, Cloud Storage, etc.).
  * `environnement` : Label `dev` ou `prod`.
  * `cout_brut` / `cout_net` : Coût avant et après crédits.

---

## 4. Stratégie de Jointure et Relations Inter-sources

Les correspondances croisées entre les différentes sources de données reposent sur des clés logiques et des mécanismes de résolution à l'étape intermédiaire :

### Jointure : France Travail ↔ Référentiel GEO (API Géo Gouv)
* **Type de jointure** : Déterministe (`INNER JOIN`)
* **Clé de jointure** : `commune_code`
* **Fichier d'implémentation** : `03_transform/dbt/models/intermediate_dev/int_ft_offres.sql`
* **Méthode** : L'API France Travail fournit directement le code commune INSEE de l'établissement d'accueil (champ `lieuTravail.commune`). Cette clé permet une jointure parfaite avec la colonne `commune_code` de la table consolidée `int_geo_communes`.

### Jointure : Adzuna ↔ Référentiel GEO (API Géo Gouv)
* **Type de jointure** : Multi-niveaux avec fallbacks (`LEFT JOIN` successifs)
* **Clé de jointure** : Nom de commune normalisé, parsing textuel ou coordonnées GPS.
* **Fichier d'implémentation** : `03_transform/dbt/models/intermediate_dev/int_adzuna_offres.sql`
* **Méthode** :
  1. *Match primaire* : Correspondance exacte du nom de ville extrait du tableau géographique Adzuna face au référentiel (`upper(a.city_name_raw) = g.commune_nom_upper`).
  2. *Fallback textuel* : Si aucun match direct, recherche d'une mention du nom d'une commune, d'un département ou d'une région française dans la chaîne textuelle brute `location_display_name` d'Adzuna.
  3. *Fallback coordonnées* : Si toujours infructueux, recherche géographique par calcul de la distance euclidienne minimale entre la `latitude`/`longitude` de l'offre Adzuna et les coordonnées moyennes de chaque commune du référentiel GEO.

### Jointure : France Travail ↔ Référentiel SIRENE (INSEE / API Entreprise)
* **Type de jointure** : Prévu en `LEFT JOIN` (actuellement simulé)
* **Clé de jointure** : Nom d'entreprise normalisé + Code Commune / Code Postal.
* **Méthode** : La jointure utilise l'API de Recherche d'Entreprises publique française. À partir du nom de l'employeur nettoyé (fourni par `int_ft_employer_names`) et de sa commune de localisation, on interroge l'API pour récupérer le SIREN et le SIRET associés, permettant de relier l'offre d'emploi à la fiche d'identité officielle de l'entreprise.

### Jointure : Adzuna ↔ API Entreprise + societe.com (Enrichissement Corporate)
* **Type de jointure** : `LEFT JOIN` déterministe
* **Clé de jointure** : `LOWER(TRIM(employer_name))` + `LOWER(TRIM(nom_commune))`
* **Fichier d'implémentation** : `03_transform/dbt/models/intermediate_dev/int_adzuna_enrichissement.sql`
* **Méthode** :
  1. *Étape d'extraction* : Les Cloud Run Jobs `api-entreprise-dev` et `n8n-trigger-dev` interrogent respectivement l'API Recherche Entreprises et societe.com (via n8n). Les résultats sont chargés dans les tables `staging_api_entreprise` et `staging_n8n_societe`.
  2. *Jointure dbt* : `int_adzuna_enrichissement` joint `int_adzuna_offres` avec ces deux tables sur le couple `(employer_name, nom_commune)` normalisé (lower + trim). Le SIREN sert de pont entre les deux sources d'enrichissement.
  3. *Consolidation dans les marts* : `mart_offres_data_jobs` hérite directement des colonnes enrichies via un LEFT JOIN sur `offer_id`. `mart_employeurs_corporate` agrège ces données au niveau entreprise pour produire une table corporate unique.
