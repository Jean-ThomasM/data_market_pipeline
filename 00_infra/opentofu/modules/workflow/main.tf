resource "google_workflows_workflow" "this" {
  project = var.project_id
  region  = var.region
  name    = var.name

  description     = var.description
  service_account = var.service_account_email
  source_contents = var.source_contents
}
