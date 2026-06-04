{{ config(
    materialized='table',
    unique_key='offer_id'
) }}

with raw_offers_base as (
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
),

raw_offers as (
    select * from (
        select 
            *,
            row_number() over (partition by offer_id order by updated_at desc, created_at desc) as rn
        from raw_offers_base
        where commune_code is not null
          and (
              upper(job_title) like '%DATA%'
              or upper(job_title) like '%DONNÉE%'
              or upper(job_title) like '%DONNÉES%'
              or upper(job_title) like '%DONNEE%'
              or upper(job_title) like '%DONNEES%'
          )
    )
    where rn = 1
),

geo_ref as (
    select 
        commune_code,
        max(code_postal) as code_postal,
        max(commune_nom) as commune_nom,
        max(departement_code) as departement_code,
        max(departement_nom) as departement_nom,
        max(region_nom) as region_nom,
        max(epci_nom) as epci_nom
    from {{ ref('int_geo_communes') }}
    group by 1
),

employer_names as (
    select offer_id, employer_name_enriched, enrichment_source
    from {{ ref('int_ft_employer_names') }}
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

        -- Employeur (enrichi via lookup + regex si entreprise.nom est NULL)
        coalesce(en.employer_name_enriched, o.employer_name) as employer_name,
        o.employer_description,
        en.enrichment_source,
        o.naf_code,
        o.industry_label,

        -- Salaire
        o.salary_label,
        o.salary_comment,

        -- Flags de qualité (format string pour compatibilité tests dbt SQLite)
        case when o.salary_label is null then '0' else '1' end as has_salary_info,
        case when upper(o.job_title) like '%ALTERNANCE%' then '1' else '0' end as is_alternance

    from raw_offers o
    inner join geo_ref g
        on o.commune_code = g.commune_code
    left join employer_names en
        on o.offer_id = en.offer_id
)

select * from final
