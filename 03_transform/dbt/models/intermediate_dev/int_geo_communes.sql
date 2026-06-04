{% if target.type == 'bigquery' and target.name == 'ci' %}

-- CI: pas de données staging → table vide
select
    cast(null as string) as commune_code,
    cast(null as string) as commune_nom,
    cast(null as string) as code_postal,
    cast(null as string) as departement_code,
    cast(null as string) as departement_nom,
    cast(null as string) as region_nom,
    cast(null as string) as epci_nom,
    cast(null as integer) as population,
    cast(null as float64) as latitude,
    cast(null as float64) as longitude
limit 0

{% elif target.type == 'bigquery' %}

with communes_raw as (
    select distinct
        code,
        nom,
        codesPostaux,
        codeDepartement,
        codeRegion,
        codeEpci,
        population,
        latitude,
        longitude
    from {{ source('geo-api', 'staging_communes') }}
),
communes_expanded as (
    select
        c.* except(codesPostaux),
        cast(cp as string) as code_postal_val
    from communes_raw c, unnest(c.codesPostaux) as cp
),
departements as (
    select distinct code, nom from {{ source('geo-api', 'staging_departements') }}
),
regions as (
    select distinct code, nom from {{ source('geo-api', 'staging_regions') }}
),
epcis as (
    select distinct code, nom from {{ source('geo-api', 'staging_epcis') }}
)
select
    trim(c.code)                        as commune_code,
    trim(c.nom)                         as commune_nom,
    trim(c.code_postal_val)             as code_postal,
    trim(d.code)                        as departement_code,
    trim(d.nom)                         as departement_nom,
    trim(r.nom)                         as region_nom,
    trim(e.nom)                         as epci_nom,
    cast(nullif(trim(cast(c.population as string)), '') as integer) as population,
    c.latitude,
    c.longitude
from communes_expanded c
left join departements d on d.code = c.codeDepartement
left join regions r on r.code = c.codeRegion
left join epcis e on e.code = c.codeEpci

{% else %}

with communes_raw as (
    select distinct
        code,
        nom,
        codesPostaux,
        codeDepartement,
        codeRegion,
        codeEpci,
        population,
        null as latitude,
        null as longitude
    from {{ source('geo-api', 'staging_communes') }}
),
communes_expanded as (
    select
        *,
        json_extract(cast(codesPostaux as text), '$[0]') as code_postal_val
    from communes_raw
),
departements as (
    select distinct code, nom from {{ source('geo-api', 'staging_departements') }}
),
regions as (
    select distinct code, nom from {{ source('geo-api', 'staging_regions') }}
),
epcis as (
    select distinct code, nom from {{ source('geo-api', 'staging_epcis') }}
)
select
    trim(c.code)                        as commune_code,
    trim(c.nom)                         as commune_nom,
    trim(c.code_postal_val)             as code_postal,
    trim(d.code)                        as departement_code,
    trim(d.nom)                         as departement_nom,
    trim(r.nom)                         as region_nom,
    trim(e.nom)                         as epci_nom,
    cast(nullif(trim(cast(c.population as string)), '') as integer) as population,
    c.latitude,
    c.longitude
from communes_expanded c
left join departements d on d.code = c.codeDepartement
left join regions r on r.code = c.codeRegion
left join epcis e on e.code = c.codeEpci

{% endif %}
