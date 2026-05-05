with offers as (
    select distinct
        cast(id as string) as offer_id,
        -- On utilise les colonnes avec double underscore __ (standard SQLite issu du loader)
        nullif(trim("lieuTravail__commune"), '') as commune_code,
        nullif(trim("lieuTravail__libelle"), '') as commune_name,
        nullif(trim("lieuTravail__codePostal"), '') as postal_code
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
