select *
from {{ ref('gold_data_engineer_marche_geo') }}
where
    part_offres_avec_salaire_pct < 0
    or part_offres_avec_salaire_pct > 100
    or part_offres_marche_pct < 0
    or part_offres_marche_pct > 100
