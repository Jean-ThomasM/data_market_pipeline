{{ config(materialized='table') }}

with staging_offres_ft as (
    select
        'Extraction' as pipeline_stage,
        'France Travail' as source_system,
        'staging_offres_ft' as table_name,
        (select count(*) from {{ source('france-travail', 'staging_offres_ft') }}) as row_count,
        38 as column_count,
        'id, intitule, description, entreprise.nom, typeContrat, salaire.libelle, romeCode' as key_columns,
        'Cle primaire, contenu, employeur type contrat, salaire, code ROME' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(id), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(intitule), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(description), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(entreprise.nom), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(salaire.libelle), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(typeContrat), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(romeCode), count(*)), 1) as fill_rate_c7,
        cast(max(dateCreation) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(dateCreation) as recency_date
        {% endif %}
    from {{ source('france-travail', 'staging_offres_ft') }}
),

staging_offres_adzuna as (
    select
        'Extraction' as pipeline_stage,
        'Adzuna' as source_system,
        'staging_offres_adzuna' as table_name,
        (select count(*) from {{ source('adzuna', 'staging_offres_adzuna') }}) as row_count,
        16 as column_count,
        'id, title, description, company, salary_min, salary_max, contract_type, location' as key_columns,
        'company = employeur, salary = remuneration, location = localisation' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(id), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(title), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(description), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(company.display_name), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(salary_min), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(salary_max), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(contract_type), count(*)), 1) as fill_rate_c7,
        cast(max(created) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(created) as recency_date
        {% endif %}
    from {{ source('adzuna', 'staging_offres_adzuna') }}
),

staging_communes as (
    select
        'Extraction' as pipeline_stage,
        'Geo' as source_system,
        'staging_communes' as table_name,
        (select count(*) from {{ source('geo-api', 'staging_communes') }}) as row_count,
        10 as column_count,
        'nom, code, codeDepartement, codesPostaux, population, latitude, longitude' as key_columns,
        '35k communes francaises, donnees publiques, mise a jour annuelle' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(nom), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(code), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(codeDepartement), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(array_length(codesPostaux)), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(population), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(latitude), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(longitude), count(*)), 1) as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% endif %}
    from {{ source('geo-api', 'staging_communes') }}
),

staging_departements as (
    select
        'Extraction' as pipeline_stage,
        'Geo' as source_system,
        'staging_departements' as table_name,
        (select count(*) from {{ source('geo-api', 'staging_departements') }}) as row_count,
        3 as column_count,
        'nom, code, codeRegion' as key_columns,
        '101 departements' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(nom), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(code), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(codeRegion), count(*)), 1) as fill_rate_c3,
        cast(null as float64) as fill_rate_c4,
        cast(null as float64) as fill_rate_c5,
        cast(null as float64) as fill_rate_c6,
        cast(null as float64) as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        null as fill_rate_c4,
        null as fill_rate_c5,
        null as fill_rate_c6,
        null as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% endif %}
    from {{ source('geo-api', 'staging_departements') }}
),

staging_regions as (
    select
        'Extraction' as pipeline_stage,
        'Geo' as source_system,
        'staging_regions' as table_name,
        (select count(*) from {{ source('geo-api', 'staging_regions') }}) as row_count,
        2 as column_count,
        'nom, code' as key_columns,
        '18 regions' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(nom), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(code), count(*)), 1) as fill_rate_c2,
        cast(null as float64) as fill_rate_c3,
        cast(null as float64) as fill_rate_c4,
        cast(null as float64) as fill_rate_c5,
        cast(null as float64) as fill_rate_c6,
        cast(null as float64) as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        null as fill_rate_c3,
        null as fill_rate_c4,
        null as fill_rate_c5,
        null as fill_rate_c6,
        null as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% endif %}
    from {{ source('geo-api', 'staging_regions') }}
),

staging_api_entreprise as (
    select
        'Enrichissement' as pipeline_stage,
        'API Entreprise' as source_system,
        'staging_api_entreprise' as table_name,
        (select count(*) from {{ source('api_entreprise', 'staging_api_entreprise') }}) as row_count,
        42 as column_count,
        'siren, nom_raison_sociale, nature_juridique, categorie, etat, finances, dirigeants' as key_columns,
        'Enrichissement corporate Adzuna, finances = REPEATED, dirigeants = REPEATED' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(siren), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(nom_raison_sociale), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(nature_juridique), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(categorie_entreprise), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(etat_administratif), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(array_length(finances)), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(array_length(dirigeants)), count(*)), 1) as fill_rate_c7,
        cast(max(enriched_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(enriched_at) as recency_date
        {% endif %}
    from {{ source('api_entreprise', 'staging_api_entreprise') }}
),

staging_n8n_societe as (
    select
        'Enrichissement' as pipeline_stage,
        'n8n Societe' as source_system,
        'staging_n8n_societe' as table_name,
        (select count(*) from {{ source('n8n_societe', 'staging_n8n_societe') }}) as row_count,
        28 as column_count,
        'siren, legal_name, naf, capital, convention_collective, dirigeants, CA, effectif' as key_columns,
        'Scraping societe.com, capital/effectif/CA = donnees financieres, dirigeants = REPEATED' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(siren), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(legal_name), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(naf_code), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(capital_social), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(convention_collective), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(chiffre_affaires), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(effectif), count(*)), 1) as fill_rate_c7,
        cast(max(scraped_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(scraped_at) as recency_date
        {% endif %}
    from {{ source('n8n_societe', 'staging_n8n_societe') }}
),

int_ft_offres as (
    select
        'Intermediaire' as pipeline_stage,
        'France Travail' as source_system,
        'int_ft_offres' as table_name,
        (select count(*) from {{ ref('int_ft_offres') }}) as row_count,
        17 as column_count,
        'offer_id, job_title, nom_commune, employer_name, contract_type, has_salary_info, naf_code' as key_columns,
        'Filtre: titre contient DATA/DONNEE, dedoublonne, georeference via int_geo_communes' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(offer_id), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(job_title), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(nom_commune), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(employer_name), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(contract_type), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(sum(cast(has_salary_info as int64)), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(naf_code), count(*)), 1) as fill_rate_c7,
        cast(max(updated_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(updated_at) as recency_date
        {% endif %}
    from {{ ref('int_ft_offres') }}
),

int_adzuna_offres as (
    select
        'Intermediaire' as pipeline_stage,
        'Adzuna' as source_system,
        'int_adzuna_offres' as table_name,
        (select count(*) from {{ ref('int_adzuna_offres') }}) as row_count,
        20 as column_count,
        'offer_id, job_title, nom_commune, employer_name, salary_min, salary_max, contract_type' as key_columns,
        'Filtre: titre DATA/DONNEE, resolution geographique 3 niveaux (exact > textuel > GPS)' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(offer_id), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(job_title), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(nom_commune), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(employer_name), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(salary_min), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(salary_max), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(contract_type), count(*)), 1) as fill_rate_c7,
        cast(max(created_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(created_at) as recency_date
        {% endif %}
    from {{ ref('int_adzuna_offres') }}
),

int_adzuna_enrichissement as (
    select
        'Intermediaire' as pipeline_stage,
        'Adzuna' as source_system,
        'int_adzuna_enrichissement' as table_name,
        (select count(*) from {{ ref('int_adzuna_enrichissement') }}) as row_count,
        25 as column_count,
        'offer_id, employer_name, siren, nom_raison_sociale, categorie_entreprise, dirigeants' as key_columns,
        'JOIN api_entreprise + n8n_societe. SIREN = taux enrichissement' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(offer_id), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(employer_name), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(siren), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(nom_raison_sociale), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(categorie_entreprise), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(ca_dernier_exercice), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(capital_social), count(*)), 1) as fill_rate_c7,
        cast(max(last_scraped_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(last_scraped_at) as recency_date
        {% endif %}
    from {{ ref('int_adzuna_enrichissement') }}
),

int_geo_communes as (
    select
        'Intermediaire' as pipeline_stage,
        'Geo' as source_system,
        'int_geo_communes' as table_name,
        (select count(*) from {{ ref('int_geo_communes') }}) as row_count,
        10 as column_count,
        'code, nom, code_postal, dept_code, dept_nom, region_nom, epci_nom' as key_columns,
        'Jointure communes + departements + regions + EPCI, une ligne par (commune, code postal)' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(commune_code), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(commune_nom), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(code_postal), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(departement_code), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(departement_nom), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(population), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(latitude), count(*)), 1) as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% endif %}
    from {{ ref('int_geo_communes') }}
),

mart_offres_data_jobs as (
    select
        'Mart' as pipeline_stage,
        'France Travail + Adzuna' as source_system,
        'mart_offres_data_jobs' as table_name,
        (select count(*) from {{ ref('mart_offres_data_jobs') }}) as row_count,
        40 as column_count,
        'offer_id, source, title, employer_name, siren, raison_sociale, salaire' as key_columns,
        'Table de faits centrale. SIREN = taux enrichissement (Adzuna). Filtres: alternance=0, cp NOT NULL' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(offer_id), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(source_system), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(job_title), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(employer_name), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(siren), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(nom_raison_sociale), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(salary_min), count(*)), 1) as fill_rate_c7,
        cast(max(created_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(created_at) as recency_date
        {% endif %}
    from {{ ref('mart_offres_data_jobs') }}
),

mart_recrutement_geographique as (
    select
        'Mart' as pipeline_stage,
        'France Travail + Adzuna' as source_system,
        'mart_recrutement_geographique' as table_name,
        (select count(*) from {{ ref('mart_recrutement_geographique') }}) as row_count,
        10 as column_count,
        'nom_region, nom_departement, nom_commune, total_offres, total_employeurs_distincts' as key_columns,
        'Aggregation geographique. Une ligne par commune avec offres Data' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(nom_region), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(nom_departement), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(nom_commune), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(total_offres), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(total_employeurs_distincts), count(*)), 1) as fill_rate_c5,
        cast(null as float64) as fill_rate_c6,
        cast(null as float64) as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        null as fill_rate_c6,
        null as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% endif %}
    from {{ ref('mart_recrutement_geographique') }}
),

mart_employeurs_corporate as (
    select
        'Mart' as pipeline_stage,
        'Adzuna' as source_system,
        'mart_employeurs_corporate' as table_name,
        (select count(*) from {{ ref('mart_employeurs_corporate') }}) as row_count,
        25 as column_count,
        'employer_name, siren, raison_sociale, nature_juridique, categorie, CA' as key_columns,
        'Fiches corporate dedupliquees par (employer, commune). Taux = completude enrichissement' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(employer_name), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(siren), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(nom_raison_sociale), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(nature_juridique), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(categorie_entreprise), count(*)), 1) as fill_rate_c5,
        round(100 * safe_divide(count(ca_dernier_exercice), count(*)), 1) as fill_rate_c6,
        round(100 * safe_divide(count(egapro_renseignee), count(*)), 1) as fill_rate_c7,
        cast(max(last_scraped_at) as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        100.0 as fill_rate_c6,
        100.0 as fill_rate_c7,
        max(last_scraped_at) as recency_date
        {% endif %}
    from {{ ref('mart_employeurs_corporate') }}
),

mart_salaires as (
    select
        'Mart' as pipeline_stage,
        'France Travail + Adzuna' as source_system,
        'mart_salaires' as table_name,
        (select count(*) from {{ ref('mart_salaires') }}) as row_count,
        10 as column_count,
        'employer_name, job_title, siren, salaire_min_moyen, salaire_max_moyen' as key_columns,
        'Analyse salariale par (employeur, poste). SIREN = taux enrichissement' as notes,
        {% if target.type == 'bigquery' %}
        round(100 * safe_divide(count(employer_name), count(*)), 1) as fill_rate_c1,
        round(100 * safe_divide(count(job_title), count(*)), 1) as fill_rate_c2,
        round(100 * safe_divide(count(siren), count(*)), 1) as fill_rate_c3,
        round(100 * safe_divide(count(salaire_min_moyen), count(*)), 1) as fill_rate_c4,
        round(100 * safe_divide(count(salaire_max_moyen), count(*)), 1) as fill_rate_c5,
        cast(null as float64) as fill_rate_c6,
        cast(null as float64) as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% else %}
        100.0 as fill_rate_c1,
        100.0 as fill_rate_c2,
        100.0 as fill_rate_c3,
        100.0 as fill_rate_c4,
        100.0 as fill_rate_c5,
        null as fill_rate_c6,
        null as fill_rate_c7,
        cast(null as timestamp) as recency_date
        {% endif %}
    from {{ ref('mart_salaires') }}
),

all_stages as (
    select * from staging_offres_ft
    union all
    select * from staging_offres_adzuna
    union all
    select * from staging_communes
    union all
    select * from staging_departements
    union all
    select * from staging_regions
    union all
    select * from staging_api_entreprise
    union all
    select * from staging_n8n_societe
    union all
    select * from int_ft_offres
    union all
    select * from int_adzuna_offres
    union all
    select * from int_adzuna_enrichissement
    union all
    select * from int_geo_communes
    union all
    select * from mart_offres_data_jobs
    union all
    select * from mart_recrutement_geographique
    union all
    select * from mart_employeurs_corporate
    union all
    select * from mart_salaires
)

select
    *,
    case
        when row_count = 0 then 'VIDE'
        when recency_date is null then 'NON_RENSEIGNE'
        {% if target.type == 'bigquery' %}
        when timestamp_diff(current_timestamp, recency_date, day) > 7 then 'STALE'
        {% else %}
        when julianday('now') - julianday(recency_date) > 7 then 'STALE'
        {% endif %}
        else 'OK'
    end as status
from all_stages
order by
    case pipeline_stage
        when 'Extraction' then 1
        when 'Enrichissement' then 2
        when 'Intermediaire' then 3
        when 'Mart' then 4
    end,
    table_name
