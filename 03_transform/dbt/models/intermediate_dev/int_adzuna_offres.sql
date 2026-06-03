{{ config(
    materialized='table',
    unique_key='offer_id'
) }}

with raw_adzuna as (
    select distinct
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
    where (
        upper(title) like '%DATA%'
        or upper(title) like '%DONNÉE%'
        or upper(title) like '%DONNÉES%'
        or upper(title) like '%DONNEE%'
        or upper(title) like '%DONNEES%'
    )
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
        max(epci_nom) as epci_nom,
        avg(latitude) as latitude,
        avg(longitude) as longitude
    from {{ ref('int_geo_communes') }}
    group by 1, 2
),

dept_ref as (
    select distinct
        departement_code,
        departement_nom,
        upper(departement_nom) as departement_nom_upper,
        region_nom
    from {{ ref('int_geo_communes') }}
),

region_ref as (
    select distinct
        region_nom,
        upper(region_nom) as region_nom_upper
    from {{ ref('int_geo_communes') }}
),

primary_matches as (
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
        a.latitude,
        a.longitude,
        a.location_display_name as original_location,
        a.dept_name_raw,
        
        -- Flags de qualité (format string pour compatibilité tests dbt SQLite)
        case when a.salary_min is null and a.salary_max is null then '0' else '1' end as has_salary_info,
        case when upper(a.job_title) like '%ALTERNANCE%' then '1' else '0' end as is_alternance,

        -- Résultats du match primaire
        g.commune_code,
        g.code_postal,
        g.commune_nom,
        g.departement_code,
        g.departement_nom,
        g.region_nom,
        g.epci_nom
    from adzuna_transformed a
    left join geo_ref g
        on upper(a.city_name_raw) = g.commune_nom_upper
        and (
            upper(a.dept_name_raw) = g.departement_nom_upper 
            or a.dept_name_raw is null 
        )
),

fallback_matches as (
    select
        p.*,
        
        -- Fallback Commune
        g_fallback.code_postal as fallback_code_postal,
        g_fallback.commune_nom as fallback_commune_nom,
        g_fallback.departement_code as fallback_commune_dept_code,
        g_fallback.departement_nom as fallback_commune_dept_nom,
        g_fallback.region_nom as fallback_commune_region_nom,
        g_fallback.epci_nom as fallback_epci_nom,
        
        -- Fallback Département
        g_fallback_dept.departement_code as fallback_dept_code,
        g_fallback_dept.departement_nom as fallback_dept_nom,
        g_fallback_dept.region_nom as fallback_dept_region_nom,
        
        -- Fallback Région
        g_fallback_region.region_nom as fallback_reg_region_nom,
        
        -- Sélection du niveau le plus précis et le plus spécifique (nom le plus long) en cas de match multiple
        row_number() over (
            partition by p.offer_id 
            order by 
                length(g_fallback.commune_nom) desc,
                length(g_fallback_dept.departement_nom) desc,
                length(g_fallback_region.region_nom) desc
        ) as rn
    from primary_matches p
    left join geo_ref g_fallback
        on p.commune_code is null
        and instr(upper(p.original_location), g_fallback.commune_nom_upper) > 0
        and (
            upper(p.dept_name_raw) = g_fallback.departement_nom_upper 
            or p.dept_name_raw is null 
        )
    left join dept_ref g_fallback_dept
        on p.commune_code is null
        and g_fallback.commune_code is null
        and instr(upper(p.original_location), g_fallback_dept.departement_nom_upper) > 0
    left join region_ref g_fallback_region
        on p.commune_code is null
        and g_fallback.commune_code is null
        and g_fallback_dept.departement_code is null
        and instr(upper(p.original_location), g_fallback_region.region_nom_upper) > 0
),

deduped_matches as (
    select * from fallback_matches where rn = 1
),

coordinate_matches as (
    select
        d.*,
        
        -- Fallback Coordonnées GPS
        g_coord.code_postal as coord_code_postal,
        g_coord.commune_nom as coord_commune_nom,
        g_coord.departement_code as coord_dept_code,
        g_coord.departement_nom as coord_dept_nom,
        g_coord.region_nom as coord_region_nom,
        g_coord.epci_nom as coord_epci_nom,
        
        -- Distance euclidienne simplifiée (suffisante pour de petites distances en France)
        row_number() over (
            partition by d.offer_id 
            order by (
                (d.latitude - g_coord.latitude) * (d.latitude - g_coord.latitude) + 
                (d.longitude - g_coord.longitude) * (d.longitude - g_coord.longitude)
            ) asc
        ) as coord_rn
    from deduped_matches d
    left join geo_ref g_coord
        on d.commune_code is null
        and d.fallback_commune_nom is null
        and d.fallback_dept_nom is null
        and d.fallback_reg_region_nom is null
        and d.latitude is not null
        and d.longitude is not null
        and g_coord.latitude is not null
        and g_coord.longitude is not null
),

deduped_coords as (
    select * from coordinate_matches where coord_rn = 1
),

final as (
    select
        offer_id,
        job_title,
        job_description,
        created_at,
        contract_time,
        contract_type,
        salary_min,
        salary_max,
        employer_name,
        category_label,
        
        -- Geographie coalescée entre le match primaire, le match textuel (fallback) et le match coordonnées
        coalesce(code_postal, fallback_code_postal, coord_code_postal) as code_postal,
        coalesce(commune_nom, fallback_commune_nom, coord_commune_nom) as nom_commune,
        
        coalesce(
            departement_code, 
            fallback_commune_dept_code, 
            fallback_dept_code,
            coord_dept_code
        ) as numero_departement,
        
        coalesce(
            departement_nom, 
            fallback_commune_dept_nom, 
            fallback_dept_nom,
            coord_dept_nom
        ) as nom_departement,
        
        coalesce(
            region_nom, 
            fallback_commune_region_nom, 
            fallback_dept_region_nom, 
            fallback_reg_region_nom,
            coord_region_nom
        ) as nom_region,
        
        coalesce(epci_nom, fallback_epci_nom, coord_epci_nom) as nom_epci,
        
        latitude,
        longitude,
        original_location,
        has_salary_info,
        is_alternance
    from deduped_coords
)

select * from final
where nom_region is not null
