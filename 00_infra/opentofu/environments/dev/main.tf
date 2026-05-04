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

module "regions_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "regions"
  schema     = file("${path.module}/schemas/regions.bqschema")
}

module "departements_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "departements"
  schema     = file("${path.module}/schemas/departements.bqschema")
}

module "communes_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "communes"
  schema     = file("${path.module}/schemas/communes.bqschema")
}

module "epcis_table" {
  source = "../../modules/bigquery_table"

  project_id = var.project_id
  dataset_id = module.staging_dataset.dataset_id
  table_id   = "epcis"
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

module "n8n_vm" {
  source = "../../modules/n8n_vm"

  project_id    = var.project_id
  region        = var.region
  zone          = var.zone
  instance_name = "n8n-dev"
}
