# Graph Report - .  (2026-05-14)

## Corpus Check
- Corpus is ~24,432 words - fits in a single context window. You may not need a graph.

## Summary
- 400 nodes · 549 edges · 49 communities (40 shown, 9 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 50 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Adzuna Scraper Pipeline|Adzuna Scraper Pipeline]]
- [[_COMMUNITY_France Travail API Client|France Travail API Client]]
- [[_COMMUNITY_France Travail Auth & Main|France Travail Auth & Main]]
- [[_COMMUNITY_dbt Project Configuration|dbt Project Configuration]]
- [[_COMMUNITY_Geo API Tests|Geo API Tests]]
- [[_COMMUNITY_Pipeline Configuration & Credentials|Pipeline Configuration & Credentials]]
- [[_COMMUNITY_Geo Scraper Pipeline|Geo Scraper Pipeline]]
- [[_COMMUNITY_FT Offer Analysis Engine|FT Offer Analysis Engine]]
- [[_COMMUNITY_FT SQLite Schema Builder|FT SQLite Schema Builder]]
- [[_COMMUNITY_Legacy FT Data Analysis|Legacy FT Data Analysis]]
- [[_COMMUNITY_France Travail OffersExtractor|France Travail OffersExtractor]]
- [[_COMMUNITY_FT Report Builder|FT Report Builder]]
- [[_COMMUNITY_France Travail Config & Auth|France Travail Config & Auth]]
- [[_COMMUNITY_Geo API Endpoints|Geo API Endpoints]]
- [[_COMMUNITY_FT SQLite Data Loader|FT SQLite Data Loader]]
- [[_COMMUNITY_Legacy Dev Analysis Scripts|Legacy Dev Analysis Scripts]]
- [[_COMMUNITY_Geo SQLite Data Loader|Geo SQLite Data Loader]]
- [[_COMMUNITY_NDJSON to SQLite Loader|NDJSON to SQLite Loader]]
- [[_COMMUNITY_Adzuna Configuration|Adzuna Configuration]]
- [[_COMMUNITY_CICD & Infrastructure|CI/CD & Infrastructure]]
- [[_COMMUNITY_dbt Intermediate Models|dbt Intermediate Models]]
- [[_COMMUNITY_Medallion Architecture Docs|Medallion Architecture Docs]]
- [[_COMMUNITY_GCS Storage Utilities|GCS Storage Utilities]]
- [[_COMMUNITY_France Travail Config Module|France Travail Config Module]]
- [[_COMMUNITY_FT Save Utilities|FT Save Utilities]]
- [[_COMMUNITY_Geo Save Utilities|Geo Save Utilities]]
- [[_COMMUNITY_Sirene API & Streamlit|Sirene API & Streamlit]]
- [[_COMMUNITY_Geo Extract & Test Bundle|Geo Extract & Test Bundle]]
- [[_COMMUNITY_Adzuna Save Utilities|Adzuna Save Utilities]]
- [[_COMMUNITY_Shared Package Init|Shared Package Init]]
- [[_COMMUNITY_Adzuna Compat Module|Adzuna Compat Module]]
- [[_COMMUNITY_FT Referential Filenames|FT Referential Filenames]]
- [[_COMMUNITY_GEO Resource Paths|GEO Resource Paths]]
- [[_COMMUNITY_Extract Package Init|Extract Package Init]]
- [[_COMMUNITY_dbt Dev Schema|dbt Dev Schema]]

## God Nodes (most connected - your core abstractions)
1. `Data Market Pipeline` - 13 edges
2. `OffersExtractor` - 10 edges
3. `build_database()` - 9 edges
4. `OffersExtractor` - 9 edges
5. `DataEngineerScraper` - 9 edges
6. `BaseFranceTravailClient` - 8 edges
7. `ReferentialsExtractor` - 7 edges
8. `GeoExtractor` - 7 edges
9. `Config` - 7 edges
10. `load_config()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `dbt Source Definitions` --references--> `GeoExtractor`  [INFERRED]
  03_transform/dbt/models/sources.yml → 02_extract/geo/scraper.py
- `Data Market Pipeline` --references--> `00_infra IaC Module`  [EXTRACTED]
  README.md → 00_infra/src/00_infra/__init__.py
- `Load FT offers to SQLite` --semantically_similar_to--> `Old FT SQLite loader`  [INFERRED] [semantically similar]
  _developpements/load_ft_to_sqlite.py → _old/load_france_travail_to_sqlite.py
- `Explore FT offers (pandas analysis)` --semantically_similar_to--> `Analyze FT fields`  [INFERRED] [semantically similar]
  _old/explore_data/analyze_offres.py → _developpements/analyze_ft_fields.py
- `dbt Source Definitions` --references--> `load_ndjson_to_sqlite`  [INFERRED]
  03_transform/dbt/models/sources.yml → 02_extract/france_travail/load_ndjson_to_sqlite.py

## Hyperedges (group relationships)
- **Sirene API Tool Suite** — sirene_streamlit, sirene_streamlit_evol, test_sirene, insee_sirene_api [INFERRED 0.90]
- **Geo Data Extraction Pipeline** — test_extract_geo_api, extract_geo_api_module, load_geo_to_sqlite_module, geo_views_sql [INFERRED 0.85]
- **Data Extraction Layer** — france_travail_extractor, geo_extractor, sirene_extractor, adzuna_extractor [EXTRACTED 1.00]
- **Orchestration Pipeline** — cloud_scheduler, cloud_workflows, cloud_run_jobs, gcs_data_lake, dbt_transform, bigquery_marts [EXTRACTED 1.00]
- **Shared Utility Dependencies** — shared_library, gcs_helpers, secrets_helpers, adzuna_load_config, adzuna_save_text_content, adzuna_scraper_2 [INFERRED 0.80]
- **Medallion Data Flow: FT Offres** — transform_SCHEMA_TRANSFORM_RawFtOffresJson, transform_SCHEMA_TRANSFORM_StagingOffresFt, transform_SCHEMA_TRANSFORM_StgFtOffresLocation, transform_SCHEMA_TRANSFORM_StgFtOffresEmployer, transform_SCHEMA_TRANSFORM_StgFtOffresSalary, transform_SCHEMA_TRANSFORM_IntFtOffresEnriched, transform_SCHEMA_TRANSFORM_MartsLayer [EXTRACTED 1.00]
- **CI/CD Pipeline Components** — semantic_release, ruff_linting, uv_lock_ci, docker_geo_api [INFERRED 0.80]

## Communities (49 total, 9 thin omitted)

### Community 0 - "Adzuna Scraper Pipeline"
Cohesion: 0.09
Nodes (39): Adzuna Config Dataclass, Adzuna OffersExtractor, Adzuna API, Adzuna extract_offers(), Adzuna Extractor, Adzuna load_config(), Adzuna request_with_retry(), Adzuna save_ndjson_records() (+31 more)

### Community 1 - "France Travail API Client"
Cohesion: 0.11
Nodes (15): BaseFranceTravailClient, Config, DataEngineerScraper, extract_francetravail_offres(), extract_francetravail_referentiels(), _parse_total(), Scraper France Travail — Offres Data Engineer + Référentiels Extraction multi-re, Logique commune : authentification, session, stockage GCS/local. (+7 more)

### Community 2 - "France Travail Auth & Main"
Cohesion: 0.13
Nodes (15): create_authenticated_session(), get_token(), refresh_access_token(), _get_extract_target(), main(), build_search_label(), extract_offers(), extract_referentials() (+7 more)

### Community 3 - "dbt Project Configuration"
Cohesion: 0.13
Nodes (20): dbt Project (data_market_pipeline), generate_schema_name Macro, dbt Profiles (multi-target), dbt Source Definitions, NDJSON-to-SQLite Default Paths, load_ndjson_to_sqlite, GEO Config Dataclass, Sirene Stub (+12 more)

### Community 4 - "Geo API Tests"
Cohesion: 0.11
Nodes (6): Vérifie que `export_geo_to_json` appelle bien les fonctions de récupération, Vérifie que `_get` construit bien l'URL complète à partir de `BASE_URL`     et q, Vérifie que `_get` transforme une `requests.HTTPError` en `RuntimeError`     ave, test_export_geo_to_json_writes_three_files(), test__get_raises_runtime_error_on_http_error(), test__get_success_builds_url_and_passes_params()

### Community 5 - "Pipeline Configuration & Credentials"
Cohesion: 0.15
Nodes (15): FranceTravailCredentials, GCPCredentials, get_gcs_bucket(), load_ft_credentials(), load_gcp_config(), load_paths(), Paths, Configuration centralisée du pipeline.  Lit les variables d'environnement et ret (+7 more)

### Community 6 - "Geo Scraper Pipeline"
Cohesion: 0.17
Nodes (8): Config, load_config(), main(), GeoExtractor, extract_geo(), GeoExtractor, Extraction des référentiels GEO depuis geo.api.gouv.fr., GEO Save Functions

### Community 7 - "FT Offer Analysis Engine"
Cohesion: 0.25
Nodes (13): analyze_offers(), build_rows(), compute_referential_match(), FieldStats, format_scalar(), infer_type(), load_offers_from_file(), load_referentials() (+5 more)

### Community 8 - "FT SQLite Schema Builder"
Cohesion: 0.27
Nodes (13): build_database(), build_flat_schema(), create_field_catalog_table(), create_flat_table(), create_raw_table(), flatten_offer(), insert_rows(), load_offers_from_file() (+5 more)

### Community 9 - "Legacy FT Data Analysis"
Cohesion: 0.16
Nodes (13): analyze_offres(), flatten_dict(), generate_column_completion_report(), load_offres_to_dataframe(), normalize_offer(), Analyse des offres France Travail - Chargement en DataFrame pandas, Affiche des statistiques de base sur les offres., Génère un rapport de complétion pour chaque colonne.      Returns:         DataF (+5 more)

### Community 10 - "France Travail OffersExtractor"
Cohesion: 0.27
Nodes (6): build_search_label(), extract_offers(), main(), OffersExtractor, Extraction des offres Adzuna avec pagination et dédoublonnage par identifiant., request_with_retry()

### Community 11 - "FT Report Builder"
Cohesion: 0.28
Nodes (11): analyze_offers(), build_report_rows(), FieldStats, format_scalar(), infer_type(), load_offers_from_file(), main(), parse_args() (+3 more)

### Community 12 - "France Travail Config & Auth"
Cohesion: 0.22
Nodes (13): create_authenticated_session, get_token (OAuth2), refresh_access_token, FranceTravail Config Dataclass, build_default_search_params, load_config (FranceTravail), FranceTravail Main Entry, OffersExtractor (+5 more)

### Community 13 - "Geo API Endpoints"
Cohesion: 0.26
Nodes (12): export_geo_to_json(), _get(), get_communes(), get_departements(), get_epcis(), get_regions(), Appelle l'API geo.api.gouv.fr avec gestion simple des erreurs., Renvoie la liste des régions.     Structure exemple:     [       {"code": "84", (+4 more)

### Community 14 - "FT SQLite Data Loader"
Cohesion: 0.22
Nodes (12): apply_france_travail_views_sql(), _infer_columns(), load_offres_json_to_raw_table(), _load_offres_list(), main(), Exécute le fichier SQL de staging des offres France Travail sur la base SQLite., Charge le dernier fichier JSON d'offres France Travail dans SQLite     et crée l, Détermine l'ensemble des clés présentes dans la liste d'offres JSON     afin de (+4 more)

### Community 15 - "Legacy Dev Analysis Scripts"
Cohesion: 0.21
Nodes (12): Analyze FT fields, Build FT offer schema (schema analysis script), Explore FT offers (pandas analysis), France Travail Offer Schema (documentation), Geo data lineage documentation, Load FT offers to SQLite, Old config settings, Old FT API extractor (+4 more)

### Community 16 - "Geo SQLite Data Loader"
Cohesion: 0.24
Nodes (11): apply_geo_views_sql(), _infer_columns(), _load_json_list(), load_json_to_raw_table(), main(), Détermine l'ensemble des clés présentes dans la liste d'objets JSON     afin de, Sérialise une valeur JSON pour stockage en TEXT dans SQLite.     - scalaires ->, Charge un fichier JSON brut dans une table SQLite "raw_*" avec     les mêmes col (+3 more)

### Community 17 - "NDJSON to SQLite Loader"
Cohesion: 0.36
Nodes (10): build_row(), create_table(), insert_rows(), iter_input_files(), load_schema(), main(), normalize_value(), parse_args() (+2 more)

### Community 18 - "Adzuna Configuration"
Cohesion: 0.44
Nodes (8): build_default_search_params(), Config, _get_local_adzuna_app_id(), _get_local_adzuna_app_key(), load_config(), _load_gcs_search_params(), _load_local_search_params(), _normalize_search_params()

### Community 19 - "CI/CD & Infrastructure"
Cohesion: 0.36
Nodes (7): v0.1.0-beta.1 Release, CI/CD Pipeline, geo_api Docker Service, Centralized Pipeline Configuration, Ruff Linting, Semantic Release, uv.lock for CI

### Community 20 - "dbt Intermediate Models"
Cohesion: 0.67
Nodes (6): Assert all offers have department (dbt test), Dual SQL Dialect Pattern, Geo Reference Enrichment Pattern, int_adzuna_offres (dbt intermediate model), int_ft_offres (dbt intermediate model), int_geo_communes (dbt intermediate model)

### Community 21 - "Medallion Architecture Docs"
Cohesion: 0.33
Nodes (6): Business Question: Data Recruitment in France, Intermediate Layer, Marts Layer, Medallion Architecture, Raw Layer, Staging Layer

### Community 22 - "GCS Storage Utilities"
Cohesion: 0.7
Nodes (4): delete_file(), _get_client(), read_file(), write_file()

### Community 23 - "France Travail Config Module"
Cohesion: 0.7
Nodes (3): build_default_search_params(), Config, load_config()

### Community 24 - "FT Save Utilities"
Cohesion: 0.6
Nodes (4): Persiste un contenu texte dans GCS, ou dans un répertoire local lorsque     le b, save_json_payload(), save_ndjson_records(), save_text_content()

### Community 25 - "Geo Save Utilities"
Cohesion: 0.6
Nodes (4): Persiste un contenu texte dans GCS, ou dans un répertoire local lorsque     le b, save_json_payload(), save_ndjson_records(), save_text_content()

## Knowledge Gaps
- **85 isolated node(s):** `Shared utilities exposed as a Python package.`, `Persiste un contenu texte dans GCS, ou dans un répertoire local lorsque     le b`, `Exécute une requête GET avec gestion homogène des erreurs réseau, des     limita`, `Extraction des référentiels France Travail.`, `Extraction des offres France Travail avec dédoublonnage par identifiant.` (+80 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Adzuna Configuration` to `France Travail Auth & Main`, `France Travail OffersExtractor`, `Geo Scraper Pipeline`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `GeoExtractor` connect `Geo Scraper Pipeline` to `Adzuna Configuration`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `GeoExtractor` connect `Geo Scraper Pipeline` to `dbt Project Configuration`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `Shared utilities exposed as a Python package.`, `Persiste un contenu texte dans GCS, ou dans un répertoire local lorsque     le b`, `Exécute une requête GET avec gestion homogène des erreurs réseau, des     limita` to the rest of the system?**
  _85 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Adzuna Scraper Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._
- **Should `France Travail API Client` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._
- **Should `France Travail Auth & Main` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._