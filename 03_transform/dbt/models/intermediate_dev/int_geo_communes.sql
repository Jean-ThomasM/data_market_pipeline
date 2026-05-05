with communes as (
    select
        nullif(trim(code), '') as commune_code,
        nullif(trim(nom), '') as commune_name,
        nullif(trim(codeDepartement), '') as departement_code,
        nullif(trim(codeRegion), '') as region_code,
        nullif(trim(codeEpci), '') as epci_code,
        safe_cast(population as int64) as population,
        nullif(trim(cast(codesPostaux[safe_offset(0)] as string)), '') as first_postal_code
    from {{ source('geo-api', 'staging_communes') }}
),
departements as (
    select
        nullif(trim(code), '') as departement_code,
        nullif(trim(nom), '') as departement_name,
        nullif(trim(codeRegion), '') as region_code
    from {{ source('geo-api', 'staging_departements') }}
),
regions as (
    select
        nullif(trim(code), '') as region_code,
        nullif(trim(nom), '') as region_name
    from {{ source('geo-api', 'staging_regions') }}
),
epcis as (
    select
        nullif(trim(code), '') as epci_code,
        nullif(trim(nom), '') as epci_name
    from {{ source('geo-api', 'staging_epcis') }}
)
select
    c.commune_code,
    c.commune_name,
    coalesce(c.departement_code, d.departement_code) as departement_code,
    d.departement_name,
    coalesce(c.region_code, d.region_code) as region_code,
    r.region_name,
    c.epci_code,
    e.epci_name,
    c.first_postal_code as postal_code,
    c.population
from communes c
left join departements d using (departement_code)
left join regions r
    on r.region_code = coalesce(c.region_code, d.region_code)
left join epcis e using (epci_code)
