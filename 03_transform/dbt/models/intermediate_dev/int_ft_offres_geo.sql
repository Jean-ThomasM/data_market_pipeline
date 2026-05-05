with offers as (
    select
        cast(id as string) as offer_id,
        nullif(trim(lieuTravail.commune), '') as commune_code,
        nullif(trim(lieuTravail.libelle), '') as commune_name,
        nullif(trim(lieuTravail.codePostal), '') as postal_code
    from {{ source('france-travail', 'staging_offres_ft') }}
),
geo_communes as (
    select * from {{ ref('int_geo_communes') }}
)
select
    o.offer_id,
    o.commune_code,
    coalesce(o.commune_name, g.commune_name) as commune_name,
    coalesce(g.departement_code, case when length(o.postal_code) >= 2 then substr(o.postal_code, 1, 2) else null end) as departement_code,
    g.departement_name,
    g.region_code,
    g.region_name,
    g.epci_code,
    g.epci_name
from offers o
left join geo_communes g
    on o.commune_code = g.commune_code
