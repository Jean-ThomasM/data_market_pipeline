output "data_lake_bucket_name" {
  value = module.data_lake.bucket_name
}

output "staging_dataset_id" {
  value = module.staging_dataset.dataset_id
}

output "intermediate_dataset_id" {
  value = module.intermediate_dataset.dataset_id
}

output "marts_dataset_id" {
  value = module.marts_dataset.dataset_id
}

output "pipeline_service_account_email" {
  value = module.pipeline_service_account.email
}

output "enabled_services" {
  value = module.project_services.enabled_services
}

output "artifact_registry_repository_url" {
  value = local.artifact_registry_repository_url
}