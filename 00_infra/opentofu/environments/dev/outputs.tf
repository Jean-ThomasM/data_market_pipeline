output "data_lake_bucket_name" {
  value = module.data_lake.bucket_name
}

output "staging_dataset_id" {
  value = module.staging_dataset.dataset_id
}

output "staging_offres_ft_table_id" {
  value = module.staging_offres_ft_table.table_id
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
  value = module.artifact_registry.repository_url
}

output "load_staging_offres_ft_workflow_name" {
  value = module.load_staging_offres_ft_workflow.name
}

output "github_workload_identity_provider" {
  description = "WIF provider resource name for GitHub Actions"
  value       = module.github_workload_identity.provider_resource_name
}

output "github_workload_identity_pool_name" {
  description = "WIF pool name"
  value       = module.github_workload_identity.pool_name
}

output "monitoring_dashboard_id" {
  description = "Pipeline monitoring dashboard resource ID"
  value       = module.pipeline_monitoring.dashboard_id
}
