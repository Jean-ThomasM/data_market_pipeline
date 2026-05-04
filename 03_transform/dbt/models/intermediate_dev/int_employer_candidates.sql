with offers as (
    select
        cast(id as string) as offer_id,
        nullif(trim(entreprise.nom), '') as employer_name,
        nullif(trim(lieuTravail.codePostal), '') as postal_code,
        nullif(trim(lieuTravail.commune), '') as commune_code,
        nullif(trim(codeNAF), '') as naf_code
    from {{ source('france-travail', 'staging_offres_ft') }}
),
normalized as (
    select
        offer_id,
        lower(trim(coalesce(employer_name, 'employeur_inconnu'))) as normalized_employer_name,
        postal_code,
        commune_code,
        naf_code
    from offers
)
select
    normalized_employer_name || '|' || coalesce(postal_code, '') || '|' || coalesce(commune_code, '') || '|' || coalesce(naf_code, '') as employer_candidate_id,
    normalized_employer_name,
    postal_code,
    commune_code,
    naf_code,
    count(distinct offer_id) as offer_count
from normalized
group by 1, 2, 3, 4, 5
