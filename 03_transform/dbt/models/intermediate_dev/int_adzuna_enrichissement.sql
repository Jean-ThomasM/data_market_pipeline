{{ config(
    materialized='table',
    unique_key='offer_id'
) }}

with base as (
    select
        offer_id,
        employer_name,
        nom_commune
    from {{ ref('int_adzuna_offres') }}
    where employer_name is not null
),

{% if target.type == 'bigquery' %}

api_entreprise as (
    select distinct
        lower(trim(employer_name)) as employer_name_key,
        lower(trim(nom_commune)) as commune_key,
        siren,
        siret_siege,
        nom_raison_sociale,
        nature_juridique,
        categorie_entreprise,
        tranche_effectif_salarie,
        annee_tranche_effectif_salarie,
        etat_administratif,
        date_creation as date_creation_entreprise,
        egapro_renseignee,
        est_ess,
        est_association,
        est_societe_mission,
        activite_principale,
        section_activite_principale,
        nombre_etablissements_ouverts,
        -- Dernier exercice financier connu
        (select f.ca from unnest(finances) as f order by f.annee desc limit 1) as ca_dernier_exercice,
        (select f.resultat_net from unnest(finances) as f order by f.annee desc limit 1) as resultat_net_dernier,
        (select max(f.annee) from unnest(finances) as f) as annee_finances,
        enriched_at as last_enriched_at
    from {{ source('api_entreprise', 'staging_api_entreprise') }}
    where siren is not null
),

n8n_societe as (
    select distinct
        lower(trim(employer_name)) as employer_name_key,
        lower(trim(nom_commune)) as commune_key,
        naf_code,
        naf_label,
        capital_social,
        convention_collective,
        chiffre_affaires,
        effectif as effectif_societe,
        scraped_at as last_scraped_at
    from {{ source('n8n_societe', 'staging_n8n_societe') }}
)

select
    base.offer_id,
    base.employer_name,
    base.nom_commune,
    a.siren,
    a.siret_siege,
    a.nom_raison_sociale,
    a.nature_juridique,
    a.categorie_entreprise,
    a.tranche_effectif_salarie,
    a.annee_tranche_effectif_salarie,
    a.etat_administratif,
    a.date_creation_entreprise,
    a.egapro_renseignee,
    a.est_ess,
    a.est_association,
    a.est_societe_mission,
    a.activite_principale,
    a.section_activite_principale,
    a.nombre_etablissements_ouverts,
    a.ca_dernier_exercice,
    a.resultat_net_dernier,
    a.annee_finances,
    a.last_enriched_at,
    n.capital_social,
    n.convention_collective,
    n.chiffre_affaires as chiffre_affaires_societe,
    n.effectif_societe,
    n.naf_code as naf_code_societe,
    n.naf_label as naf_label_societe,
    n.last_scraped_at
from base
left join api_entreprise a
    on lower(trim(base.employer_name)) = a.employer_name_key
    and lower(trim(base.nom_commune)) = a.commune_key
left join n8n_societe n
    on lower(trim(base.employer_name)) = n.employer_name_key
    and lower(trim(base.nom_commune)) = n.commune_key

{% else %}

-- Fallback SQLite: pas de données d'enrichissement disponibles
select
    offer_id,
    employer_name,
    nom_commune,
    cast(null as text) as siren,
    cast(null as text) as siret_siege,
    cast(null as text) as nom_raison_sociale,
    cast(null as text) as nature_juridique,
    cast(null as text) as categorie_entreprise,
    cast(null as text) as tranche_effectif_salarie,
    cast(null as text) as annee_tranche_effectif_salarie,
    cast(null as text) as etat_administratif,
    cast(null as text) as date_creation_entreprise,
    cast(null as integer) as egapro_renseignee,
    cast(null as integer) as est_ess,
    cast(null as integer) as est_association,
    cast(null as integer) as est_societe_mission,
    cast(null as text) as activite_principale,
    cast(null as text) as section_activite_principale,
    cast(null as integer) as nombre_etablissements_ouverts,
    cast(null as real) as ca_dernier_exercice,
    cast(null as real) as resultat_net_dernier,
    cast(null as text) as annee_finances,
    cast(null as text) as last_enriched_at,
    cast(null as text) as capital_social,
    cast(null as text) as convention_collective,
    cast(null as text) as chiffre_affaires_societe,
    cast(null as text) as effectif_societe,
    cast(null as text) as naf_code_societe,
    cast(null as text) as naf_label_societe,
    cast(null as text) as last_scraped_at
from base

{% endif %}
