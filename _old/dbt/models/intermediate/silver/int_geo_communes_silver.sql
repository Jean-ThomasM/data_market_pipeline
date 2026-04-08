select
    trim(c.nom) as commune_nom,
    trim(json_extract(c.codesPostaux, '$[0]')) as code_postal,
    trim(d.code) as departement_code,
    trim(d.nom) as departement_nom,
    trim(r.nom) as region_nom,
    trim(e.nom) as epci_nom,
    cast(nullif(c.population, '') as integer) as population
from {{ source('geo', 'raw_geo_communes') }} as c
left join {{ source('geo', 'raw_geo_departements') }} as d
    on d.code = c.codeDepartement
left join {{ source('geo', 'raw_geo_regions') }} as r
    on r.code = c.codeRegion
left join {{ source('geo', 'raw_geo_epcis') }} as e
    on e.code = c.codeEpci
