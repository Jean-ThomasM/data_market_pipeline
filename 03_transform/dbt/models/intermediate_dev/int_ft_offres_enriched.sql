with base_offres as (
    select distinct
        cast(id as string) as offer_id,
        intitule as job_title,
        dateCreation as created_at,
        typeContrat as contract_type,
        {% if target.type == 'bigquery' %}
        salaire.libelle as salary_label,
        {% else %}
        {{ adapter.quote('salaire__libelle') }} as salary_label,
        {% endif %}
        case
            {% if target.type == 'bigquery' %}
            when salaire.libelle is null then 'missing_salary'
            {% else %}
            when {{ adapter.quote('salaire__libelle') }} is null then 'missing_salary'
            {% endif %}
            else 'salary_present'
        end as salary_quality_flag
    from {{ source('france-travail', 'staging_offres_ft') }}
),
geo as (
    select * from {{ ref('int_ft_offres_geo') }}
),
employers as (
    select * from {{ ref('int_ft_offres_employers_matched') }}
)
select
    b.offer_id,
    b.job_title,
    b.created_at,
    b.contract_type,
    g.region_nom,
    e.siren,
    e.legal_name,
    b.salary_label,
    b.salary_quality_flag
from base_offres b
left join geo g using (offer_id)
left join employers e using (offer_id)
