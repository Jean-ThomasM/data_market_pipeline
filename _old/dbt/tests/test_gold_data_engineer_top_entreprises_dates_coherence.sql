select *
from {{ ref('gold_data_engineer_top_entreprises') }}
where
    premiere_date_offre is not null
    and derniere_actualisation is not null
    and derniere_actualisation < premiere_date_offre
