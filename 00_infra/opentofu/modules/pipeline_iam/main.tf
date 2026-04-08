resource "google_storage_bucket_iam_member" "pipeline_storage_object_admin" {
  bucket = var.bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}

resource "google_project_iam_member" "pipeline_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${var.service_account_email}"
}

resource "google_project_iam_member" "pipeline_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${var.service_account_email}"
}

resource "google_project_iam_member" "pipeline_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.service_account_email}"
}