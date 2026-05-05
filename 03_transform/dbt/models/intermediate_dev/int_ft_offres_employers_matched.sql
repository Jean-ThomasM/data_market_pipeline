with offers as (
    select distinct
        cast(id as string) as offer_id,
        {% if target.type == 'bigquery' %}
        lower(trim(coalesce(nullif(trim(entreprise.nom), ''), 'employeur_inconnu'))) as normalized_employer_name,
        nullif(trim(lieuTravail.codePostal), '') as postal_code,
        nullif(trim(lieuTravail.commune), '') as commune_code,
        {% else %}
        lower(trim(coalesce(nullif(trim({{ adapter.quote('entreprise__nom') }}), ''), 'employeur_inconnu'))) as normalized_employer_name,
        nullif(trim({{ adapter.quote('lieuTravail__codePostal') }}), '') as postal_code,
        nullif(trim({{ adapter.quote('lieuTravail__commune') }}), '') as commune_code,
        {% endif %}
        nullif(trim(codeNAF), '') as naf_code
    from {{ source('france-travail', 'staging_offres_ft') }}
)
select
    offer_id,
    normalized_employer_name || '|' || coalesce(postal_code, '') || '|' || coalesce(commune_code, '') || '|' || coalesce(naf_code, '') as employer_candidate_id,
    cast(null as string) as siren,
    cast(null as string) as siret,
    cast(null as string) as legal_name,
    cast(0 as float64) as match_confidence,
    'unmatched' as match_status
from offers
