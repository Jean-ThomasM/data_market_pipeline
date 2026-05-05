-- Ce test verifie que toutes les offres qui ont un code commune ou un code postal 
-- arrivent a trouver un departement dans le referentiel geo.
-- S'il y a des resultats, le test echoue.

select
    offer_id,
    commune_code,
    postal_code
from {{ ref('int_ft_offres_geo') }}
where (commune_code is not null or postal_code is not null)
  and departement_nom is null
