with base as (
    select
        r.*,
        nullif(trim(id), '') as offre_id,
        "salaire__listeComplements" as salaire_liste_complements,
        "contexteTravail__horaires" as contexte_horaires,
        qualitesProfessionnelles as qualites_professionnelles
    from {{ source('france_travail', 'raw_ft_offres') }} as r
    where nullif(trim(id), '') is not null
),
competences as (
    select
        b.offre_id,
        count(*) as nb_competences,
        group_concat(distinct nullif(trim(json_extract(j.value, '$.libelle')), '')) as competences_libelles
    from base as b
    join json_each(case when json_valid(b.competences) then b.competences else '[]' end) as j
    group by b.offre_id
),
langues as (
    select
        b.offre_id,
        count(*) as nb_langues,
        group_concat(distinct nullif(trim(json_extract(j.value, '$.libelle')), '')) as langues_libelles
    from base as b
    join json_each(case when json_valid(b.langues) then b.langues else '[]' end) as j
    group by b.offre_id
),
permis as (
    select
        b.offre_id,
        count(*) as nb_permis,
        group_concat(distinct nullif(trim(json_extract(j.value, '$.libelle')), '')) as permis_libelles
    from base as b
    join json_each(case when json_valid(b.permis) then b.permis else '[]' end) as j
    group by b.offre_id
),
qualites as (
    select
        b.offre_id,
        count(*) as nb_qualites_professionnelles,
        group_concat(distinct nullif(trim(json_extract(j.value, '$.libelle')), '')) as qualites_professionnelles_libelles
    from base as b
    join json_each(case when json_valid(b.qualites_professionnelles) then b.qualites_professionnelles else '[]' end) as j
    group by b.offre_id
),
salaire_complements as (
    select
        b.offre_id,
        count(*) as nb_salaire_complements,
        group_concat(distinct nullif(trim(json_extract(j.value, '$.libelle')), '')) as salaire_complements_libelles
    from base as b
    join json_each(case when json_valid(b.salaire_liste_complements) then b.salaire_liste_complements else '[]' end) as j
    group by b.offre_id
),
horaires as (
    select
        b.offre_id,
        count(*) as nb_horaires,
        group_concat(distinct nullif(trim(j.value), '')) as horaires_libelles
    from base as b
    join json_each(case when json_valid(b.contexte_horaires) then b.contexte_horaires else '[]' end) as j
    group by b.offre_id
)
{% set dict_cols_sql = select_clean_flattened_dict_columns(source('france_travail', 'raw_ft_offres'), 'b') %}
select
    -- Ensemble complet des colonnes raw_ft_offres
    b.*,
    -- Toutes les colonnes dictionnaires deja aplanies (parent__enfant) sont nettoyees automatiquement.
    {% if dict_cols_sql | trim %}
    {{ dict_cols_sql }},
    {% endif %}
    -- Colonnes listes eclatees / agregees
    coalesce(c.nb_competences, 0) as nb_competences,
    c.competences_libelles,
    coalesce(l.nb_langues, 0) as nb_langues,
    l.langues_libelles,
    coalesce(p.nb_permis, 0) as nb_permis,
    p.permis_libelles,
    coalesce(q.nb_qualites_professionnelles, 0) as nb_qualites_professionnelles,
    q.qualites_professionnelles_libelles,
    coalesce(sc.nb_salaire_complements, 0) as nb_salaire_complements,
    sc.salaire_complements_libelles,
    coalesce(h.nb_horaires, 0) as nb_horaires,
    h.horaires_libelles
from base as b
left join competences as c on c.offre_id = b.offre_id
left join langues as l on l.offre_id = b.offre_id
left join permis as p on p.offre_id = b.offre_id
left join qualites as q on q.offre_id = b.offre_id
left join salaire_complements as sc on sc.offre_id = b.offre_id
left join horaires as h on h.offre_id = b.offre_id
