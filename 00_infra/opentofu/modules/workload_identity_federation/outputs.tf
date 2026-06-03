output "pool_name" {
  description = "WIF pool resource name"
  value       = google_iam_workload_identity_pool.github.name
}

output "provider_resource_name" {
  description = "Full resource name of the OIDC provider (for GitHub Actions workload_identity_provider)"
  value = "projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github.workload_identity_pool_provider_id}"
}

output "provider_id" {
  description = "Short provider ID"
  value       = google_iam_workload_identity_pool_provider.github.workload_identity_pool_provider_id
}

output "pool_id" {
  description = "Short pool ID"
  value       = google_iam_workload_identity_pool.github.workload_identity_pool_id
}
