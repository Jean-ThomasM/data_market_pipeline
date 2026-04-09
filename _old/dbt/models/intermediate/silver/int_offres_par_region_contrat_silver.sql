with base as (
    select *
    from {{ ref('int_ft_offre_geo_silver') }}
),
agg as (
    select
        coalesce(region_nom, 'Non renseignee') as region_nom,
        coalesce(type_contrat_libelle, 'Non renseigne') as type_contrat_libelle,
        count(*) as offres_total,
        count(distinct offre_id) as offres_uniques,
        count(distinct entreprise_nom) as entreprises_uniques,
        round(avg(cast(nombre_postes as real)), 2) as moyenne_nombre_postes
    from base
    group by 1, 2
),
tot as (
    select sum(offres_total) as grand_total
    from agg
)
select
    a.region_nom,
    a.type_contrat_libelle,
    a.offres_total,
    a.offres_uniques,
    a.entreprises_uniques,
    a.moyenne_nombre_postes,
    round(100.0 * a.offres_total / nullif(t.grand_total, 0), 2) as part_offres_pct
from agg as a
cross join tot as t
order by a.offres_total desc
