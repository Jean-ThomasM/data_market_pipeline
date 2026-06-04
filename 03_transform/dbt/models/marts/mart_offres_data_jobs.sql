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
        null as salary_min,
        null as salary_max,
        has_salary_info,
        is_alternance
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
