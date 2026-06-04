{{ config(
    materialized='table',
    unique_key='offer_id'
) }}

{% if target.type == 'bigquery' %}

with name_ref as (
    select distinct trim(nom) as nom from (
        select entreprise.nom
        from {{ source('france-travail', 'staging_offres_ft') }}
        where entreprise.nom is not null and length(trim(entreprise.nom)) > 3
        union distinct
        select company.display_name
        from {{ source('adzuna', 'staging_offres_adzuna') }}
        where company.display_name is not null and length(trim(company.display_name)) > 3
    )
    where length(trim(nom)) > 3
        and lower(trim(nom)) not in (
            select w from unnest([
                'the','and','for','sas','sarl','eurl','sa','saas',
                'groupe','solutions','services','france','monde',
                'europe','paris','rh','drh','com'
            ]) as w
        )
        and regexp_contains(trim(nom), r'[A-Za-z]')
        and not regexp_contains(trim(nom), r'\\')
),

ft_offers as (
    select
        cast(id as string) as offer_id,
        nullif(trim(entreprise.nom), '') as employer_name_raw,
        nullif(trim(entreprise.description), '') as employer_description,
        regexp_replace(entreprise.description, r'<[^>]+>', '') as description_clean
    from {{ source('france-travail', 'staging_offres_ft') }}
    where entreprise.description is not null
),

to_enrich as (
    select * from ft_offers
    where employer_name_raw is null
),

lookup_matches as (
    select
        f.offer_id,
        any_value(r.nom) as employer_name_lookup
    from to_enrich f
    join name_ref r on regexp_contains(
        lower(f.description_clean),
        concat(r'\b', lower(regexp_replace(r.nom, r'([.+*?^$()|\[\]{}])', r'\\\1')), r'\b')
    )
    group by f.offer_id
),

regex_matches as (
    select
        offer_id,
        description_clean,
        coalesce(
            regexp_extract(description_clean, r'Rejoindre ([A-Z][A-Za-z0-9-]+(?: [A-Z][A-Za-z0-9-]+){0,2})'),
            regexp_extract(description_clean, r'(?:Filiale|Acteur|Leader|Cabinet|Groupe|Societe|Expert|Specialiste|Entreprise) (?:du|de |des )?([A-Z][A-Za-z0-9-]+(?: [A-Z][A-Za-z0-9-]+){0,2})'),
            regexp_extract(description_clean, r'^\s*([A-Z][A-Za-z0-9-]+(?: [A-Z][A-Za-z0-9-]+)*) est (?:un|une)'),
            regexp_extract(description_clean, r'^[^,]+,[ ]*([A-Z][A-Za-z0-9-]+(?: [A-Z][A-Za-z0-9-]+)*) est'),
            regexp_extract(description_clean, r'raison d&rsquo;&ecirc;tre d&rsquo;([A-Z]+)')
        ) as employer_name_regex
    from to_enrich
)

select
    f.offer_id,
    f.employer_name_raw,
    f.employer_description,
    coalesce(
        l.employer_name_lookup,
        r.employer_name_regex
    ) as employer_name_enriched,
    case
        when f.employer_name_raw is not null then 'raw'
        when l.employer_name_lookup is not null then 'lookup'
        when r.employer_name_regex is not null then 'regex'
        else 'fallback'
    end as enrichment_source
from ft_offers f
left join lookup_matches l on f.offer_id = l.offer_id
left join regex_matches r on f.offer_id = r.offer_id

{% else %}

-- SQLite fallback: no enrichment, raw pass-through
select
    cast(id as string) as offer_id,
    nullif(trim(entreprise_nom), '') as employer_name_raw,
    nullif(trim(entreprise_description), '') as employer_description,
    cast(null as string) as employer_name_enriched,
    cast(null as string) as enrichment_source
from {{ source('france-travail', 'staging_offres_ft') }}
where entreprise_description is not null

{% endif %}

