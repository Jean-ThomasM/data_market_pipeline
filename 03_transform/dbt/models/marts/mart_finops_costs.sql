{{ config(
    schema='finops_dev',
    materialized='table'
) }}

{% if target.type == 'bigquery' %}

{% set billing_exists = false %}
{% if execute %}
  {% set check_query %}
    select count(*) > 0 as has_table
    from `{{ target.project }}.finops_dev.INFORMATION_SCHEMA.TABLES`
    where table_name like 'gcp_billing_export%'
  {% endset %}
  {% set results = run_query(check_query) %}
  {% set billing_exists = results.rows[0].has_table %}
{% endif %}

{% if billing_exists %}

{% set billing_table %}
  (select table_name
   from `{{ target.project }}.INFORMATION_SCHEMA.TABLES`
   where table_catalog = '{{ target.project }}'
     and table_schema = 'finops_dev'
     and table_name like 'gcp_billing_export%'
   limit 1)
{% endset %}

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
        sum(cost + coalesce((select sum(amount) from unnest(credits)), 0)) as cout_net,
        currency
    from `{{ target.project }}.finops_dev.gcp_billing_export_v1_*`
    where project.id = '{{ target.project }}'
    group by 1, 2, 3, 4, 5, 6, 7, 10
)

select * from billing

{% else %}

select
    cast(null as string) as facturation_mois,
    cast(null as date) as date_usage,
    cast(null as string) as service_nom,
    cast(null as string) as ressource_sku,
    cast(null as string) as gcp_project_id,
    cast(null as string) as environnement,
    cast(null as string) as projet_nom,
    cast(null as float64) as cout_brut,
    cast(null as float64) as cout_net,
    cast(null as string) as currency
limit 0

{% endif %}

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
