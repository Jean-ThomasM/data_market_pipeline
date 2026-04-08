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