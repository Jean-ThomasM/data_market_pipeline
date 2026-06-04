{{ config(
    materialized='table'
) }}

with base as (
    select
        employer_name,
        nom_commune,
        job_title,
        salary_min,
        salary_max,
        siren,
        nom_raison_sociale,
        nature_juridique,
        categorie_entreprise
    from {{ ref('mart_offres_data_jobs') }}
    where salary_min is not null or salary_max is not null
)

select
    employer_name,
    nom_commune,
    job_title,
    siren,
    nom_raison_sociale,
    nature_juridique,
    categorie_entreprise,
    count(*) as nombre_offres,
    {% if target.type == 'bigquery' %}
    min(salary_min) as salaire_min_global,
    max(salary_max) as salaire_max_global,
    avg(salary_min) as salaire_min_moyen,
    avg(salary_max) as salaire_max_moyen,
    {% else %}
    min(salary_min) as salaire_min_global,
    max(salary_max) as salaire_max_global,
    avg(salary_min) as salaire_min_moyen,
    avg(salary_max) as salaire_max_moyen,
    {% endif %}
    avg(salary_max) - avg(salary_min) as ecart_moyen
from base
group by 1, 2, 3, 4, 5, 6, 7
