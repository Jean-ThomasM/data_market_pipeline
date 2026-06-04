{{ config(
    materialized='table'
) }}

with fact_offers as (
    select * from {{ ref('mart_offres_data_jobs') }}
),

aggregated as (
    select
        employer_name,
        count(*) as total_offres,
        avg(salary_min) as salaire_min_moyen,
        avg(salary_max) as salaire_max_moyen,
        sum(cast(has_salary_info as int)) as total_offres_avec_salaire
    from fact_offers
    group by 1
)

select
    employer_name,
    total_offres,
    total_offres_avec_salaire,
    round(salaire_min_moyen, 2) as salaire_min_moyen,
    round(salaire_max_moyen, 2) as salaire_max_moyen
from aggregated
