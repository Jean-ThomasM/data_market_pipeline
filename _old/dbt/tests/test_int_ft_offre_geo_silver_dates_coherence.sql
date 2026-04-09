select *
from {{ ref('int_ft_offre_geo_silver') }}
where
    date_creation is not null
    and date_actualisation is not null
    and date_actualisation < date_creation
