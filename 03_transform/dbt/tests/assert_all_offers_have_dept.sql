-- Ce test verifie que toutes les offres qui ont un code commune ou un code postal 
-- arrivent a trouver un departement dans le referentiel geo.
-- S'il y a des resultats, le test echoue.

select
    offer_id,
    code_postal,
    nom_departement
from {{ ref('int_ft_offres') }}
where nom_departement is null
