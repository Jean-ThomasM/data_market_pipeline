-- Modèles SQL de la couche STAGING pour les données géographiques
-- Ces vues supposent que les fichiers CSV produits par
-- `geo_api/transform_geo_json.py` sont exposés comme tables externes
-- ou chargés dans des tables brutes équivalentes.

-- Exemple d'hypothèse de nommage des tables sources :
--   raw_geo_regions, raw_geo_departements, raw_geo_communes, raw_geo_communes_codes_postaux, raw_geo_epcis

DROP VIEW IF EXISTS stg_geo_regions;
CREATE VIEW stg_geo_regions AS
SELECT
    trim(region_code) AS region_code,
    trim(region_nom)  AS region_nom
FROM raw_geo_regions;


DROP VIEW IF EXISTS stg_geo_departements;
CREATE VIEW stg_geo_departements AS
SELECT
    trim(departement_code) AS departement_code,
    trim(departement_nom)  AS departement_nom,
    trim(region_code)      AS region_code
FROM raw_geo_departements;


DROP VIEW IF EXISTS stg_geo_communes;
CREATE VIEW stg_geo_communes AS
SELECT
    trim(commune_code)     AS commune_code,
    trim(commune_nom)      AS commune_nom,
    trim(departement_code) AS departement_code,
    trim(region_code)      AS region_code,
    CAST(NULLIF(population, '') AS INTEGER) AS population
FROM raw_geo_communes;


DROP VIEW IF EXISTS stg_geo_communes_codes_postaux;
CREATE VIEW stg_geo_communes_codes_postaux AS
SELECT
    trim(commune_code) AS commune_code,
    trim(code_postal)  AS code_postal
FROM raw_geo_communes_codes_postaux;


DROP VIEW IF EXISTS stg_geo_epcis;
CREATE VIEW stg_geo_epcis AS
SELECT
    trim(epci_code)   AS epci_code,
    trim(epci_nom)    AS epci_nom,
    trim(region_code) AS region_code,
    trim(nature)      AS nature
FROM raw_geo_epcis;

