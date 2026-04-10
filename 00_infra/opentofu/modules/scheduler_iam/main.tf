resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${var.service_account_email}"
}

resource "google_project_iam_member" "scheduler_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${var.service_account_email}"
}