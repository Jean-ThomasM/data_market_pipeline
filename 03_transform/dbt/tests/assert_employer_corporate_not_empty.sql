-- Vérifie que la table corporate n'est pas vide
select count(*) as nb_rows
from {{ ref('mart_employeurs_corporate') }}
having count(*) = 0
