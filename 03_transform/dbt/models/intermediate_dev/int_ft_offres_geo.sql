with offers as (
    select
        cast(id as string) as offer_id,
        nullif(trim(lieuTravail_commune), '') as commune_code,
        nullif(trim(lieuTravail_libelle), '') as commune_name,
        nullif(trim(lieuTravail_codePostal), '') as postal_code
    from {{ source('france-travail', 'staging_offres_ft') }}
)
select
    offer_id,
    commune_code,
    commune_name,
    case when length(postal_code) >= 2 then substr(postal_code, 1, 2) else null end as departement_code,
    cast(null as string) as departement_name,
    cast(null as string) as region_code,
    cast(null as string) as region_name,
    cast(null as string) as epci_code,
    cast(null as string) as epci_name
from offers
