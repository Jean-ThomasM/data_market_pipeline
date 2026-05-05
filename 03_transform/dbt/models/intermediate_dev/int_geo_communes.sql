with communes_raw as (
    select distinct
        code,
        nom,
        codesPostaux,
        codeDepartement,
        codeRegion,
        codeEpci,
        population
    from {{ source('geo-api', 'staging_communes') }}
),
-- On éclate les codes postaux pour avoir une ligne par couple (commune, cp)
-- Sur BigQuery on utilise UNNEST. 
-- Pour SQLite local, on simule ou on utilise le premier si UNNEST n'est pas supporté.
communes_expanded as (
    {% if adapter.plugin_name == 'bigquery' %}
    select 
        c.* except(codesPostaux),
        cast(cp as string) as code_postal_val
    from communes_raw c, unnest(c.codesPostaux) as cp
    {% else %}
    -- Version SQLite simplifiée (on prend le premier pour ne pas casser l'exécution locale)
    select 
        *,
        json_extract(codesPostaux, '$[0]') as code_postal_val
    from communes_raw
    {% endif %}
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
    trim(c.code)                                as commune_code,
    trim(c.nom)                                 as commune_nom,
    trim(c.code_postal_val)                     as code_postal,
    trim(d.code)                                as departement_code,
    trim(d.nom)                                 as departement_nom,
    trim(r.nom)                                 as region_nom,
    trim(e.nom)                                 as epci_nom,
    cast(nullif(trim(cast(c.population as string)), '') as integer) as population
from communes_expanded c
left join departements d
    on d.code = c.codeDepartement
left join regions r
    on r.code = c.codeRegion
left join epcis e
    on e.code = c.codeEpci
