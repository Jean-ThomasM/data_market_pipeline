with base as (
    select *
    from {{ ref('int_ft_offre_geo_silver') }}
),
filtered as (
    select *
    from base
    where
        lower(coalesce(rome_libelle, '')) like '%data%'
        or lower(coalesce(intitule, '')) like '%data engineer%'
        or lower(coalesce(intitule, '')) like '%ingenieur data%'
),
agg as (
    select
        coalesce(region_nom, 'Non renseignee') as region_nom,
        coalesce(departement_code, 'Non renseigne') as departement_code,
        coalesce(departement_nom, 'Non renseigne') as departement_nom,
        coalesce(type_contrat_libelle, 'Non renseigne') as type_contrat_libelle,
        count(*) as offres_total,
        count(distinct entreprise_nom) as entreprises_uniques,
        count(distinct offre_id) as offres_uniques,
        sum(case when salaire_libelle is not null then 1 else 0 end) as offres_avec_salaire,
        -- Placeholder pour futures donnees numeriques de salaire.
        cast(null as real) as salaire_min_eur,
        cast(null as real) as salaire_max_eur,
        cast(null as real) as salaire_median_eur
    from filtered
    group by 1, 2, 3, 4
),
tot as (
    select sum(offres_total) as total_offres
    from agg
)
select
    a.region_nom,
    a.departement_code,
    a.departement_nom,
    a.type_contrat_libelle,
    a.offres_total,
    a.entreprises_uniques,
    a.offres_uniques,
    a.offres_avec_salaire,
    round(100.0 * a.offres_avec_salaire / nullif(a.offres_total, 0), 2) as part_offres_avec_salaire_pct,
    round(100.0 * a.offres_total / nullif(t.total_offres, 0), 2) as part_offres_marche_pct,
    a.salaire_min_eur,
    a.salaire_max_eur,
    a.salaire_median_eur
from agg as a
cross join tot as t
order by a.offres_total desc
