{{ config(
    materialized='table'
) }}

with enriched_offers as (
    select
        employer_name,
        nom_commune,
        siren,
        siret_siege,
        nom_raison_sociale,
        nature_juridique,
        categorie_entreprise,
        tranche_effectif_salarie,
        annee_tranche_effectif_salarie,
        etat_administratif,
        date_creation_entreprise,
        egapro_renseignee,
        est_ess,
        est_association,
        est_societe_mission,
        nombre_etablissements_ouverts,
        ca_dernier_exercice,
        resultat_net_dernier,
        annee_finances,
        capital_social,
        convention_collective,
        chiffre_affaires_societe,
        effectif_societe,
        last_enriched_at,
        last_scraped_at,
        salary_min,
        salary_max
    from {{ ref('mart_offres_data_jobs') }}
    where source_system = 'Adzuna'
),

aggregated as (
    select
        lower(trim(employer_name)) as employer_name_key,
        lower(trim(nom_commune)) as commune_key,
        -- Identité : on prend la première valeur non nulle
        max(employer_name) as employer_name,
        max(nom_commune) as nom_commune,
        max(siren) as siren,
        max(siret_siege) as siret_siege,
        max(nom_raison_sociale) as nom_raison_sociale,
        max(nature_juridique) as nature_juridique,
        max(categorie_entreprise) as categorie_entreprise,
        max(tranche_effectif_salarie) as tranche_effectif_salarie,
        max(annee_tranche_effectif_salarie) as annee_tranche_effectif_salarie,
        max(etat_administratif) as etat_administratif,
        max(date_creation_entreprise) as date_creation_entreprise,

        -- RSE
        max(cast(egapro_renseignee as int)) as egapro_renseignee,
        max(cast(est_ess as int)) as est_ess,
        max(cast(est_association as int)) as est_association,
        max(cast(est_societe_mission as int)) as est_societe_mission,

        -- Structure
        max(nombre_etablissements_ouverts) as nombre_etablissements_ouverts,
        max(capital_social) as capital_social,
        max(convention_collective) as convention_collective,
        max(chiffre_affaires_societe) as chiffre_affaires_societe,
        max(effectif_societe) as effectif_societe,

        -- Financier
        max(ca_dernier_exercice) as ca_dernier_exercice,
        max(resultat_net_dernier) as resultat_net_dernier,
        max(annee_finances) as annee_finances,

        -- Timestamps
        max(last_enriched_at) as last_enriched_at,
        max(last_scraped_at) as last_scraped_at,

        -- Recrutement
        count(*) as total_offres,
        avg(salary_min) as salaire_min_moyen,
        avg(salary_max) as salaire_max_moyen
    from enriched_offers
    group by 1, 2
)

select
    employer_name,
    nom_commune,
    siren,
    siret_siege,
    nom_raison_sociale,
    nature_juridique,
    categorie_entreprise,
    tranche_effectif_salarie,
    annee_tranche_effectif_salarie,
    etat_administratif,
    date_creation_entreprise,
    egapro_renseignee,
    est_ess,
    est_association,
    est_societe_mission,
    nombre_etablissements_ouverts,
    capital_social,
    convention_collective,
    chiffre_affaires_societe,
    effectif_societe,
    ca_dernier_exercice,
    resultat_net_dernier,
    annee_finances,
    last_enriched_at,
    last_scraped_at,
    total_offres,
    {% if target.type == 'bigquery' %}
    round(salaire_min_moyen, 2) as salaire_min_moyen,
    round(salaire_max_moyen, 2) as salaire_max_moyen
    {% else %}
    round(salaire_min_moyen, 2) as salaire_min_moyen,
    round(salaire_max_moyen, 2) as salaire_max_moyen
    {% endif %}
from aggregated
where employer_name is not null
