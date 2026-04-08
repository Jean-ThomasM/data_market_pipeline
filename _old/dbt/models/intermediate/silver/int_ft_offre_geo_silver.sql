with offres_normalized as (
    select
        nullif(trim(o.id), '') as offre_id,
        nullif(trim(o.intitule), '') as intitule,
        nullif(trim(o.description), '') as description,
        nullif(trim(o.romeCode), '') as rome_code,
        nullif(trim(o.romeLibelle), '') as rome_libelle,
        nullif(trim(o.appellationlibelle), '') as appellation_libelle,
        nullif(trim(o."lieuTravail__commune"), '') as commune_code,
        nullif(trim(o."lieuTravail__codePostal"), '') as code_postal,
        nullif(trim(o."lieuTravail__libelle"), '') as lieu_libelle,
        nullif(trim(o."entreprise__nom"), '') as entreprise_nom,
        nullif(trim(o.typeContrat), '') as type_contrat_code,
        nullif(trim(o.typeContratLibelle), '') as type_contrat_libelle,
        nullif(trim(o.natureContrat), '') as nature_contrat,
        date(nullif(trim(o.dateCreation), '')) as date_creation,
        date(nullif(trim(o.dateActualisation), '')) as date_actualisation,
        nullif(trim(o.secteurActivite), '') as secteur_activite_code,
        nullif(trim(o.secteurActiviteLibelle), '') as secteur_activite_libelle,
        nullif(trim(o."salaire__libelle"), '') as salaire_libelle,
        nullif(trim(o.dureeTravailLibelle), '') as duree_travail_libelle,
        nullif(trim(o.dureeTravailLibelleConverti), '') as duree_travail_libelle_converti,
        cast(nullif(trim(o.nombrePostes), '') as integer) as nombre_postes,
        case
            when lower(trim(o.alternance)) in ('true', '1', 'oui') then 1
            when lower(trim(o.alternance)) in ('false', '0', 'non') then 0
            else null
        end as alternance,
        case
            when lower(trim(o.accessibleTH)) in ('true', '1', 'oui') then 1
            when lower(trim(o.accessibleTH)) in ('false', '0', 'non') then 0
            else null
        end as accessible_th,
        nullif(trim(o.qualificationCode), '') as qualification_code,
        nullif(trim(o.qualificationLibelle), '') as qualification_libelle,
        nullif(trim(o."origineOffre__origine"), '') as origine_offre_code,
        nullif(trim(o."origineOffre__urlOrigine"), '') as origine_offre_url
    from {{ source('france_travail', 'raw_ft_offres') }} as o
    where nullif(trim(o.id), '') is not null
),
offres_dedup as (
    select *
    from (
        select
            o.*,
            row_number() over (
                partition by o.offre_id
                order by o.date_actualisation desc, o.date_creation desc
            ) as rn
        from offres_normalized as o
    )
    where rn = 1
)
select
    o.offre_id,
    o.intitule,
    o.description,
    o.rome_code,
    o.rome_libelle,
    o.appellation_libelle,
    o.commune_code,
    o.code_postal,
    o.lieu_libelle,
    o.entreprise_nom,
    o.type_contrat_code,
    o.type_contrat_libelle,
    o.nature_contrat,
    o.date_creation,
    o.date_actualisation,
    o.secteur_activite_code,
    o.secteur_activite_libelle,
    o.salaire_libelle,
    o.duree_travail_libelle,
    o.duree_travail_libelle_converti,
    o.nombre_postes,
    o.alternance,
    o.accessible_th,
    o.qualification_code,
    o.qualification_libelle,
    o.origine_offre_code,
    o.origine_offre_url,
    trim(d.nom) as departement_nom,
    trim(r.nom) as region_nom,
    trim(e.nom) as epci_nom
from offres_dedup as o
left join {{ source('geo', 'raw_geo_communes') }} as c
    on c.code = o.commune_code
left join {{ source('geo', 'raw_geo_departements') }} as d
    on d.code = c.codeDepartement
left join {{ source('geo', 'raw_geo_regions') }} as r
    on r.code = c.codeRegion
left join {{ source('geo', 'raw_geo_epcis') }} as e
    on e.code = c.codeEpci
where o.commune_code is not null
