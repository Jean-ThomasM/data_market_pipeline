with offers as (
    select distinct
        cast(id as string) as offer_id,
        {% if target.type == 'bigquery' %}
        nullif(trim(lieuTravail.commune), '') as commune_code,
        nullif(trim(lieuTravail.libelle), '') as commune_name,
        nullif(trim(lieuTravail.codePostal), '') as postal_code
        {% else %}
        -- SQLite local: colonnes aplaties avec "__"
        nullif(trim({{ adapter.quote('lieuTravail__commune') }}), '') as commune_code,
        nullif(trim({{ adapter.quote('lieuTravail__libelle') }}), '') as commune_name,
        nullif(trim({{ adapter.quote('lieuTravail__codePostal') }}), '') as postal_code
        {% endif %}
    from {{ source('france-travail', 'staging_offres_ft') }}
),
geo_communes as (
    -- On s'appuie sur le référentiel propre
    select * from {{ ref('int_geo_communes') }}
)
select
    o.offer_id,
    o.commune_code,
    o.postal_code,
    -- Priorité aux infos du référentiel GÉO (int_geo_communes)
    coalesce(g.commune_nom, o.commune_name) as commune_name,
    g.departement_code,
    g.departement_nom,
    g.region_nom,
    g.epci_nom
from offers o
left join geo_communes g
    on o.commune_code = g.commune_code
    and o.postal_code = g.code_postal
