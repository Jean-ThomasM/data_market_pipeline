{{ config(
    materialized='table',
    unique_key='offer_id'
) }}

with raw_adzuna as (
    select
        cast(id as string) as offer_id,
        title as job_title,
        description as job_description,
        created as created_at,
        {% if target.type == 'bigquery' %}
        redirect_url,
        salary_is_predicted,
        contract_time,
        contract_type,
        salary_min,
        salary_max,
        latitude,
        longitude,
        company.display_name as employer_name,
        location.display_name as location_display_name,
        location.area as location_area,
        category.label as category_label
        {% else %}
        -- Fallback SQLite (champs aplatis attendus)
        null as redirect_url,
        salary_is_predicted,
        contract_time,
        contract_type,
        salary_min,
        salary_max,
        latitude,
        longitude,
        company_display_name as employer_name,
        location_display_name,
        location_area,
        category_label
        {% endif %}
    from {{ source('adzuna', 'staging_offres_adzuna') }}
),

adzuna_transformed as (
    select
        *,
        {% if target.type == 'bigquery' %}
        -- Extraction de la ville (le plus précis dans l'array area, généralement le dernier)
        case 
            when array_length(location_area) > 1 
            then location_area[safe_offset(array_length(location_area) - 1)]
            else null 
        end as city_name_raw,
        
        -- Extraction du département (l'avant-dernier si disponible)
        case 
            when array_length(location_area) > 2
            then location_area[safe_offset(array_length(location_area) - 2)]
            else null 
        end as dept_name_raw
        {% else %}
        -- SQLite : extraction simplifiée via le display_name (ex: "Marseille, Bouches-du-Rhône")
        case 
            when instr(location_display_name, ',') > 0 
            then trim(substr(location_display_name, 1, instr(location_display_name, ',') - 1))
            else location_display_name 
        end as city_name_raw,
        case 
            when instr(location_display_name, ',') > 0 
            then trim(substr(location_display_name, instr(location_display_name, ',') + 1))
            else null 
        end as dept_name_raw
        {% endif %}
    from raw_adzuna
),

geo_ref as (
    -- On déduplique le référentiel par nom de commune et nom de département 
    -- pour éviter les produits cartésiens avec les codes postaux multiples
    select 
        upper(commune_nom) as commune_nom_upper,
        upper(departement_nom) as departement_nom_upper,
        max(commune_code) as commune_code,
        max(commune_nom) as commune_nom,
        max(code_postal) as code_postal,
        max(departement_code) as departement_code,
        max(departement_nom) as departement_nom,
        max(region_nom) as region_nom,
        max(epci_nom) as epci_nom
    from {{ ref('int_geo_communes') }}
    group by 1, 2
),

final as (
    select
        a.offer_id,
        a.job_title,
        a.job_description,
        a.created_at,
        a.contract_time,
        a.contract_type,
        a.salary_min,
        a.salary_max,
        a.employer_name,
        a.category_label,
        
        -- Geographie (Structure identique à int_ft_offres)
        g.code_postal,
        g.commune_nom as nom_commune,
        g.departement_code as numero_departement,
        g.departement_nom as nom_departement,
        g.region_nom as nom_region,
        g.epci_nom as nom_epci,
        
        -- Coordonnées originales Adzuna
        a.latitude,
        a.longitude,

        -- Métadonnées additionnelles
        a.location_display_name as original_location,
        
        -- Flags de qualité
        case when a.salary_min is null and a.salary_max is null then 0 else 1 end as has_salary_info
        
    from adzuna_transformed a
    inner join geo_ref g
        on upper(a.city_name_raw) = g.commune_nom_upper
        and (
            upper(a.dept_name_raw) = g.departement_nom_upper 
            or a.dept_name_raw is null 
        )
)

select * from final
