{{ config(
    materialized='table'
) }}

with fact_offers as (
    select * from {{ ref('mart_offres_data_jobs') }}
),

offers_with_salary as (
    select
        nom_region,
        contract_type,
        salary_min,
        salary_max,
        case
            when salary_min is not null and salary_max is not null then (salary_min + salary_max) / 2.0
            when salary_min is not null then salary_min
            else salary_max
        end as salary_avg
    from fact_offers
    where salary_min is not null or salary_max is not null
)

select
    nom_region,
    contract_type,
    count(*) as total_offres_avec_salaire,
    round(avg(salary_min), 2) as salaire_min_moyen,
    round(avg(salary_max), 2) as salaire_max_moyen,
    round(avg(salary_avg), 2) as salaire_moyen
from offers_with_salary
group by 1, 2
