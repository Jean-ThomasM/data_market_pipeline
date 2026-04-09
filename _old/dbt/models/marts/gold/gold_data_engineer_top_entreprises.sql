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
        coalesce(entreprise_nom, 'Entreprise non renseignee') as entreprise_nom,
        coalesce(region_nom, 'Non renseignee') as region_nom,
        count(*) as offres_total,
        count(distinct type_contrat_libelle) as nb_types_contrat,
        sum(case when salaire_libelle is not null then 1 else 0 end) as offres_avec_salaire,
        min(date_creation) as premiere_date_offre,
        max(date_actualisation) as derniere_actualisation
    from filtered
    group by 1, 2
)
select
    entreprise_nom,
    region_nom,
    offres_total,
    nb_types_contrat,
    offres_avec_salaire,
    round(100.0 * offres_avec_salaire / nullif(offres_total, 0), 2) as part_offres_avec_salaire_pct,
    premiere_date_offre,
    derniere_actualisation
from agg
where offres_total >= 2
order by offres_total desc, entreprise_nom
