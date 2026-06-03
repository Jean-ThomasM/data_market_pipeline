{{ config(
    materialized='table'
) }}

with fact_offers as (
    select * from {{ ref('mart_offres_data_jobs') }}
),

aggregated as (
    select
        nom_region,
        nom_departement,
        nom_commune,
        count(*) as total_offres,
        count(distinct employer_name) as total_employeurs_distincts,
        sum(case when upper(contract_type) = 'CDI' then 1 else 0 end) as total_cdi,
        sum(case when is_alternance = 1 then 1 else 0 end) as total_alternance,
        sum(has_salary_info) as total_offres_avec_salaire
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
    case 
        when total_offres > 0 
        then round(cast(total_cdi as float) / total_offres * 100, 2) 
        else 0 
    end as pct_cdi,
    case 
        when total_offres > 0 
        then round(cast(total_alternance as float) / total_offres * 100, 2) 
        else 0 
    end as pct_alternance,
    case 
        when total_offres > 0 
        then round(cast(total_offres_avec_salaire as float) / total_offres * 100, 2) 
        else 0 
    end as complitude_salaire_pct
from aggregated
