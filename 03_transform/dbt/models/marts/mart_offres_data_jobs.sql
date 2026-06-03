{{ config(
    materialized='table'
) }}

with adzuna_offers as (
    select
        offer_id,
        'Adzuna' as source_system,
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
        salary_min,
        salary_max,
        has_salary_info,
        is_alternance
    from {{ ref('int_adzuna_offres') }}
)

select * from adzuna_offers
where code_postal is not null
  and is_alternance = '0'
