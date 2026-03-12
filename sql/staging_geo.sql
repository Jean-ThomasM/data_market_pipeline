-- Modèles SQL de la couche STAGING pour les données géographiques
-- Ces vues supposent que les fichiers CSV produits par
-- `geo_api/transform_geo_json.py` sont exposés comme tables externes
-- ou chargés dans des tables brutes équivalentes.

-- Exemple d'hypothèse de nommage des tables sources :
--   raw_geo_regions, raw_geo_departements, raw_geo_communes, raw_geo_communes_codes_postaux, raw_geo_epcis

create or replace view stg_geo_regions as
select
    trim(region_code) as region_code,
    trim(region_nom)  as region_nom
from raw_geo_regions;


create or replace view stg_geo_departements as
select
    trim(departement_code) as departement_code,
    trim(departement_nom)  as departement_nom,
    trim(region_code)      as region_code
from raw_geo_departements;


create or replace view stg_geo_communes as
select
    trim(commune_code)    as commune_code,
    trim(commune_nom)     as commune_nom,
    trim(departement_code) as departement_code,
    trim(region_code)     as region_code,
    cast(nullif(population, '') as integer) as population
from raw_geo_communes;


create or replace view stg_geo_communes_codes_postaux as
select
    trim(commune_code) as commune_code,
    trim(code_postal)  as code_postal
from raw_geo_communes_codes_postaux;


create or replace view stg_geo_epcis as
select
    trim(epci_code)  as epci_code,
    trim(epci_nom)   as epci_nom,
    trim(region_code) as region_code,
    trim(nature)     as nature
from raw_geo_epcis;

