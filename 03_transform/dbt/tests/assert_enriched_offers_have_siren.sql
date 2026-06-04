-- Vérifie que les offres Adzuna enrichies ont un SIREN
select offer_id
from {{ ref('mart_offres_data_jobs') }}
where source_system = 'Adzuna'
  and siren is null
