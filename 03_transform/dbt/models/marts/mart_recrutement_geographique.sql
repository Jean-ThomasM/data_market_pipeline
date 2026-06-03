{{ config(
    materialized='table'
) }}

with fact_offers as (
    select * from {{ ref('mart_offres_data_jobs') }}
    where has_salary_info = '1'
),

aggregated as (
    select
        nom_region,
        nom_departement,
        nom_commune,
        count(*) as total_offres,
        count(distinct employer_name) as total_employeurs_distincts,
        sum(case when upper(contract_type) = 'CDI' then 1 else 0 end) as total_cdi,
        sum(case when is_alternance = '1' then 1 else 0 end) as total_alternance,
        sum(cast(has_salary_info as int)) as total_offres_avec_salaire,
        
        -- Moyennes de salaires min et max
        avg(salary_min) as salaire_min_moyen,
        avg(salary_max) as salaire_max_moyen
    from fact_offers
    group by 1, 2, 3
)

select
    nom_region,
    nom_departement,
    nom_commune,
    total_offres,
    total_employeurs_distincts,
    total_cdi,
    total_alternance,
    total_offres_avec_salaire,
    round(salaire_min_moyen, 2) as salaire_min_moyen,
    round(salaire_max_moyen, 2) as salaire_max_moyen,
    case 
        when total_offres > 0 
        then round(cast(total_cdi as float64) / total_offres * 100, 2) 
        else 0 
    end as pct_cdi,
    case 
        when total_offres > 0 
        then round(cast(total_alternance as float64) / total_offres * 100, 2) 
        else 0 
    end as pct_alternance,
    case 
        when total_offres > 0 
        then round(cast(total_offres_avec_salaire as float64) / total_offres * 100, 2) 
        else 0 
    end as complitude_salaire_pct
from aggregated
