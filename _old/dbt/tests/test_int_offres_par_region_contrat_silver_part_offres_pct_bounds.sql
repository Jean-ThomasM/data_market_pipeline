select *
from {{ ref('int_offres_par_region_contrat_silver') }}
where part_offres_pct < 0 or part_offres_pct > 100
