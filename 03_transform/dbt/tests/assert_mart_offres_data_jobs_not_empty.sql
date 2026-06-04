-- Ce test vérifie que la table mart_offres_data_jobs contient des enregistrements.
-- Si la table est vide, le test renvoie une ligne et échoue.

with count_records as (
    select count(*) as cnt from {{ ref('mart_offres_data_jobs') }}
)
select 1 from count_records where cnt = 0
