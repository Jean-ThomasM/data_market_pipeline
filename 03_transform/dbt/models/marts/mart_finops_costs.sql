{{ config(
    schema='finops_dev',
    materialized='table'
) }}

{% if target.type == 'bigquery' %}

with billing as (
    select
        invoice.month as facturation_mois,
        date(usage_start_time) as date_usage,
        service.description as service_nom,
        sku.description as ressource_sku,
        project.id as gcp_project_id,
        (
            select value from unnest(labels) where key = 'environment'
        ) as environnement,
        (
            select value from unnest(labels) where key = 'project'
        ) as projet_nom,
        sum(cost) as cout_brut,
        sum(cost) + sum(credits.amount) as cout_net,
        currency
    from `data-market-386959.billing_raw.gcp_billing_export_v1_*`
    where project.id = 'data-market-386959'
    group by 1, 2, 3, 4, 5, 6, 7, 10
)

select * from billing

{% else %}

select
    cast(null as text) as facturation_mois,
    cast(null as text) as date_usage,
    cast(null as text) as service_nom,
    cast(null as text) as ressource_sku,
    cast(null as text) as gcp_project_id,
    cast(null as text) as environnement,
    cast(null as text) as projet_nom,
    cast(null as real) as cout_brut,
    cast(null as real) as cout_net,
    cast(null as text) as currency
limit 0

{% endif %}
