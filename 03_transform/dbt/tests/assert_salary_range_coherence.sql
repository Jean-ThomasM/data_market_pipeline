-- Ce test vérifie que le salaire maximum n'est pas inférieur au salaire minimum.
-- Si des lignes sont retournées, le test échoue.

select
    offer_id,
    salary_min,
    salary_max
from {{ ref('int_adzuna_offres') }}
where salary_min is not null 
  and salary_max is not null 
  and salary_max < salary_min
