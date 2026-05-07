data "google_project" "current" {
  project_id = var.project_id
}

module "data_lake" {
  source = "../../modules/gcs_bucket"

  name               = "${var.project_id}-data-lake-${var.environment}"
  location           = var.bucket_location
  versioning_enabled = true
}

module "staging_dataset" {
  source = "../../modules/bigquery_dataset"

  dataset_id = "staging_${var.environment}"
  location   = var.bigquery_location
}

module "intermediate_dataset" {
  source = "../../modules/bigquery_dataset"

  dataset_id = "intermediate_${var.environment}"
  location   = var.bigquery_location
}

module "marts_dataset" {
  source = "../../modules/bigquery_dataset"

  dataset_id = "marts_${var.environment}"
  location   = var.bigquery_location
}

module "staging_offres_ft_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "staging_offres_ft"
  schema     = file("${path.module}/schemas/staging_offres_ft.bqschema")
}

module "staging_offres_adzuna_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "staging_offres_adzuna"
  schema     = file("${path.module}/schemas/staging_offres_adzuna.bqschema")
}

module "regions_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "staging_regions"
  schema     = file("${path.module}/schemas/regions.bqschema")
}

module "departements_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "staging_departements"
  schema     = file("${path.module}/schemas/departements.bqschema")
}

module "communes_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "staging_communes"
  schema     = file("${path.module}/schemas/communes.bqschema")
}

module "epcis_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "staging_epcis"
  schema     = file("${path.module}/schemas/epcis.bqschema")
}

module "load_staging_offres_ft_workflow" {
  source = "../../modules/workflow"

  project_id            = var.project_id
  region                = var.region
  name                  = "load-staging-offres-ft-${var.environment}"
  description           = "Charge les offres France Travail depuis GCS vers BigQuery."
  service_account_email = module.pipeline_service_account.email
  source_contents = templatefile(
    "${path.module}/workflows/load_staging_offres_ft.yaml.tftpl",
    {
      project_id  = var.project_id
      dataset_id  = module.staging_dataset.dataset_id
      table_id    = module.staging_offres_ft_table.table_id
      bucket_name = module.data_lake.bucket_name
    }
  )

  depends_on = [
    module.project_services,
    google_project_service_identity.workflows_service_agent,
    google_service_account_iam_member.workflows_service_account_token_creator
  ]
}

module "load_staging_adzuna_workflow" {
  source = "../../modules/workflow"

  project_id            = var.project_id
  region                = var.region
  name                  = "load-staging-adzuna-${var.environment}"
  description           = "Charge les offres Adzuna depuis GCS vers BigQuery."
  service_account_email = module.pipeline_service_account.email
  source_contents = templatefile(
    "${path.module}/workflows/load_staging_adzuna.yaml.tftpl",
    {
      project_id  = var.project_id
      dataset_id  = module.staging_dataset.dataset_id
      table_id    = module.staging_offres_adzuna_table.table_id
      bucket_name = module.data_lake.bucket_name
    }
  )

  depends_on = [
    module.staging_offres_adzuna_table,
    module.project_services,
    google_project_service_identity.workflows_service_agent,
    google_service_account_iam_member.workflows_service_account_token_creator
  ]
}

module "load_staging_geo_workflow" {
  source = "../../modules/workflow"

  project_id            = var.project_id
  region                = var.region
  name                  = "load-staging-geo-${var.environment}"
  description           = "Charge les données GEO depuis GCS vers BigQuery."
  service_account_email = module.pipeline_service_account.email
  source_contents = templatefile(
    "${path.module}/workflows/load_staging_geo.yaml.tftpl",
    {
      project_id  = var.project_id
      dataset_id  = module.staging_dataset.dataset_id
      bucket_name = module.data_lake.bucket_name
    }
  )

  depends_on = [
    module.regions_table,
    module.departements_table,
    module.communes_table,
    module.epcis_table,
    module.project_services,
    google_project_service_identity.workflows_service_agent,
    google_service_account_iam_member.workflows_service_account_token_creator
  ]
}

module "pipeline_service_account" {
  source = "../../modules/service_account"

  account_id   = "pipeline-runner-${var.environment}"
  display_name = "Pipeline Runner ${var.environment}"
}

module "project_services" {
  source = "../../modules/project_services"

  project_id = var.project_id

  services = [
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "workflows.googleapis.com",
    "cloudscheduler.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ]
}

module "artifact_registry" {
  source = "../../modules/artifact_registry"

  project_id    = var.project_id
  location      = var.region
  repository_id = "data-market-docker-repository"
  description   = "Docker images for data pipelines in dev"
}

module "extract_job_ft" {
  source = "../../modules/cloud_run_job"

  project_id = var.project_id
  region     = var.region

  job_name = "extract-ft-dev"

  image = "${module.artifact_registry.repository_url}/extract-ft:latest"

  service_account_email = module.pipeline_service_account.email

  env_vars = {
    ENVIRONMENT             = var.environment
    BUCKET_NAME             = module.data_lake.bucket_name
    DATASET_ID              = module.staging_dataset.dataset_id
    GCP_PROJECT_ID          = var.project_id
    GCS_BUCKET_NAME         = module.data_lake.bucket_name
    FT_EXTRACT_TARGET       = "offers"
    FT_SEARCH_PARAMS_OBJECT = "config/search_params_prod.json"
    STORAGE                 = "gcs"
  }
}

module "extract_job_geo" {
  source = "../../modules/cloud_run_job"

  project_id = var.project_id
  region     = var.region

  job_name = "extract-geo-dev"

  image = "${module.artifact_registry.repository_url}/extract-geo:latest"

  service_account_email = module.pipeline_service_account.email

  env_vars = {
    ENVIRONMENT     = var.environment
    BUCKET_NAME     = module.data_lake.bucket_name
    DATASET_ID      = module.staging_dataset.dataset_id
    GCP_PROJECT_ID  = var.project_id
    GCS_BUCKET_NAME = module.data_lake.bucket_name
    STORAGE         = "gcs"
    GEO_API_URL     = "https://geo.api.gouv.fr/"
  }
}

module "extract_job_adzuna" {
  source = "../../modules/cloud_run_job"

  project_id = var.project_id
  region     = var.region

  job_name = "extract-adzuna-dev"

  image = "${module.artifact_registry.repository_url}/extract-adzuna:latest"

  service_account_email = module.pipeline_service_account.email

  env_vars = {
    ENVIRONMENT     = var.environment
    BUCKET_NAME     = module.data_lake.bucket_name
    DATASET_ID      = module.staging_dataset.dataset_id
    GCP_PROJECT_ID  = var.project_id
    GCS_BUCKET_NAME = module.data_lake.bucket_name
    STORAGE         = "gcs"
  }
}

module "pipeline_iam" {
  source = "../../modules/pipeline_iam"

  project_id            = var.project_id
  bucket_name           = module.data_lake.bucket_name
  service_account_email = module.pipeline_service_account.email
}

module "ft_client_id_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "FT_CLIENT_ID"
}

module "ft_client_key_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "FT_CLIENT_KEY"
}

module "adzuna_client_id_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "ADZUNA_API_ID"
}

module "adzuna_client_key_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "ADZUNA_API_KEY"
}

resource "google_project_service_identity" "workflows_service_agent" {
  provider = google-beta

  project = var.project_id
  service = "workflows.googleapis.com"

  depends_on = [module.project_services]
}

resource "google_service_account_iam_member" "workflows_service_account_token_creator" {
  service_account_id = module.pipeline_service_account.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-workflows.iam.gserviceaccount.com"

  depends_on = [google_project_service_identity.workflows_service_agent]
}

resource "google_project_iam_member" "pipeline_workflows_invoker" {
  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${module.pipeline_service_account.email}"
}

module "dbt_service_account" {
  source = "../../modules/service_account"

  account_id   = "dbt-runner-${var.environment}"
  display_name = "dbt Runner ${var.environment}"
}

module "dbt_iam" {
  source = "../../modules/dbt_iam"

  project_id            = var.project_id
  service_account_email = module.dbt_service_account.email
}

module "dbt_env_secret" {
  source = "../../modules/secret_manager_secret"

  project_id = var.project_id
  secret_id  = "DBT_ENV_SECRET"
}

module "dbt_job" {
  source = "../../modules/cloud_run_job"

  project_id = var.project_id
  region     = var.region

  job_name = "dbt-run-${var.environment}"

  image = "${var.region}-docker.pkg.dev/${var.project_id}/data-market-docker-repository/dbt_transform:latest"

  service_account_email = module.dbt_service_account.email

  env_vars = {
    DBT_TARGET_ENV = var.environment
    GCP_PROJECT_ID = var.project_id
  }
}

module "pipeline_global_workflow" {
  source                = "../../modules/workflow"
  project_id            = var.project_id
  region                = var.region
  name                  = "pipeline-global-${var.environment}"
  description           = "Orchestre extraction FT/GEO/ADZUNA et chargement staging."
  service_account_email = module.pipeline_service_account.email

  source_contents = templatefile(
    "${path.module}/workflows/pipeline_global.yaml.tftpl",
    {
      project_id                = var.project_id
      region                    = var.region
      environment               = var.environment
      extract_ft_job_name       = module.extract_job_ft.job_name
      extract_geo_job_name      = module.extract_job_geo.job_name
      extract_adzuna_job_name   = module.extract_job_adzuna.job_name
      load_ft_workflow_name     = module.load_staging_offres_ft_workflow.name
      load_geo_workflow_name    = module.load_staging_geo_workflow.name
      load_adzuna_workflow_name = module.load_staging_adzuna_workflow.name
    }
  )

  depends_on = [
    module.extract_job_ft,
    module.extract_job_geo,
    module.extract_job_adzuna,
    module.load_staging_offres_ft_workflow,
    module.load_staging_geo_workflow,
    module.load_staging_adzuna_workflow,
    module.pipeline_iam,
    module.project_services,
    google_project_service_identity.workflows_service_agent,
    google_service_account_iam_member.workflows_service_account_token_creator,
    google_project_iam_member.pipeline_workflows_invoker
  ]
}

module "n8n_service_account" {
  source = "../../modules/service_account"

  account_id   = "n8n-runner-${var.environment}"
  display_name = "n8n Runner ${var.environment}"
}

module "n8n_service" {
  source = "../../modules/cloud_run_service"

  project_id = var.project_id
  region     = var.region

  service_name = "n8n-${var.environment}"

  image = "docker.io/n8nio/n8n:latest"

  service_account_email = module.n8n_service_account.email

  cpu    = "2"
  memory = "4Gi"

  env_vars = {
    N8N_PORT            = "5678"
    N8N_PROTOCOL        = "https"
    N8N_HOST            = "n8n-dev-5pko4kkvvq-ew.a.run.app"
    WEBHOOK_URL         = "https://n8n-dev-5pko4kkvvq-ew.a.run.app"
    N8N_EDITOR_BASE_URL = "https://n8n-dev-5pko4kkvvq-ew.a.run.app"
    N8N_PUSH_BACKEND    = "sse"
  }
}

resource "google_cloud_run_service_iam_member" "n8n_public_access" {
  project  = var.project_id
  location = var.region
  service  = module.n8n_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}