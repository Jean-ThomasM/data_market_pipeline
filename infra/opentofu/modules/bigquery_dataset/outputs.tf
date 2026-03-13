output "dataset_id" {
  description = "ID du dataset BigQuery"
  value       = google_bigquery_dataset.this.dataset_id
}