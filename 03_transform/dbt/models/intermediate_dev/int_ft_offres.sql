{{ config(
    materialized='table',
    unique_key='offer_id'
) }}

with raw_offers as (
    select 
        cast(id as string) as offer_id,
        intitule as job_title,
        description as job_description,
        dateCreation as created_at,
        dateActualisation as updated_at,
        typeContrat as contract_type,
        experienceExige as experience_required,
        {% if target.type == 'bigquery' %}
        nullif(trim(entreprise.nom), '') as employer_name,
        nullif(trim(entreprise.description), '') as employer_description,
        nullif(trim(lieuTravail.commune), '') as commune_code,
        nullif(trim(lieuTravail.codePostal), '') as code_postal,
        nullif(trim(lieuTravail.libelle), '') as commune_label,
        nullif(trim(salaire.libelle), '') as salary_label,
        nullif(trim(salaire.commentaire), '') as salary_comment,
        {% else %}
        -- SQLite: Utilisation du simple underscore '_' comme séparateur identifié via DBeaver
        nullif(trim(entreprise_nom), '') as employer_name,
        nullif(trim(entreprise_description), '') as employer_description,
        nullif(trim(lieuTravail_commune), '') as commune_code,
        nullif(trim(lieuTravail_codePostal), '') as code_postal,
        nullif(trim(lieuTravail_libelle), '') as commune_label,
        null as salary_label,
        null as salary_comment,
        {% endif %}
        nullif(trim(codeNAF), '') as naf_code,
        secteurActiviteLibelle as industry_label
    from {{ source('france-travail', 'staging_offres_ft') }}
    where commune_code is not null
),

geo_ref as (
    select * from {{ ref('int_geo_communes') }}
),

final as (
    select
        o.offer_id,
        o.job_title,
        o.job_description,
        o.created_at,
        o.updated_at,
        o.contract_type,
        o.experience_required,
        
        -- Geographie (Source unique : référentiel GÉO, jointure sur code INSEE)
        g.code_postal,
        g.commune_nom as nom_commune,
        g.departement_code as numero_departement,
        g.departement_nom as nom_departement,
        g.region_nom as nom_region,
        g.epci_nom as nom_epci,

        -- Employeur
        o.employer_name,
        o.employer_description,
        o.naf_code,
        o.industry_label,

        -- Salaire
        o.salary_label,
        o.salary_comment,

        -- Flags de qualité
        case when o.salary_label is null then 0 else 1 end as has_salary_info,
        case when g.commune_code is null then 0 else 1 end as is_geo_matched

    from raw_offers o
    inner join geo_ref g
        on o.commune_code = g.commune_code
)

select * from final
