{{ config(
    materialized='table'
) }}

with adzuna_offers as (
    select
        a.offer_id,
        'Adzuna' as source_system,
        a.job_title,
        a.job_description,
        a.created_at,
        a.contract_type,
        a.code_postal,
        a.nom_commune,
        a.numero_departement,
        a.nom_departement,
        a.nom_region,
        a.nom_epci,
        a.employer_name,
        a.category_label,
        a.salary_min,
        a.salary_max,
        a.has_salary_info,
        a.is_alternance,
        e.siren,
        e.siret_siege,
        e.nom_raison_sociale,
        e.nature_juridique,
        e.categorie_entreprise,
        e.tranche_effectif_salarie,
        e.annee_tranche_effectif_salarie,
        e.etat_administratif,
        e.date_creation_entreprise,
        e.egapro_renseignee,
        e.est_ess,
        e.est_association,
        e.est_societe_mission,
        e.nombre_etablissements_ouverts,
        e.ca_dernier_exercice,
        e.resultat_net_dernier,
        e.annee_finances,
        e.capital_social,
        e.convention_collective,
        e.chiffre_affaires_societe,
        e.effectif_societe,
        e.activite_principale,
        e.section_activite_principale,
        e.naf_code_societe,
        e.naf_label_societe
    from {{ ref('int_adzuna_offres') }} as a
    left join {{ ref('int_adzuna_enrichissement') }} as e
        on a.offer_id = e.offer_id
),

ft_offers as (
    select
        offer_id,
        'France Travail' as source_system,
        job_title,
        job_description,
        created_at,
        contract_type,
        code_postal,
        nom_commune,
        numero_departement,
        nom_departement,
        nom_region,
        nom_epci,
        employer_name,
        null as category_label,
        null as salary_min,
        null as salary_max,
        has_salary_info,
        is_alternance,
        null as siren,
        null as siret_siege,
        null as nom_raison_sociale,
        null as nature_juridique,
        null as categorie_entreprise,
        null as tranche_effectif_salarie,
        null as annee_tranche_effectif_salarie,
        null as etat_administratif,
        null as date_creation_entreprise,
        null as egapro_renseignee,
        null as est_ess,
        null as est_association,
        null as est_societe_mission,
        null as activite_principale,
        null as section_activite_principale,
        null as nombre_etablissements_ouverts,
        null as ca_dernier_exercice,
        null as resultat_net_dernier,
        null as annee_finances,
        null as capital_social,
        null as convention_collective,
        null as chiffre_affaires_societe,
        null as effectif_societe,
        null as naf_code_societe,
        null as naf_label_societe,
        naf_code,
        industry_label
    from {{ ref('int_ft_offres') }}
),

all_offers as (
    select * from adzuna_offers
    union all
    select * from ft_offers
)

select * from all_offers
where
    code_postal is not null
    and is_alternance = '0'
