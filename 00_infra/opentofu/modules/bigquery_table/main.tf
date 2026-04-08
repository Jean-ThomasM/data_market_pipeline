resource "google_bigquery_table" "this" {
  dataset_id = var.dataset_id
  table_id   = var.table_id
  project    = var.project_id

  deletion_protection = var.deletion_protection
  schema              = var.schema
}
