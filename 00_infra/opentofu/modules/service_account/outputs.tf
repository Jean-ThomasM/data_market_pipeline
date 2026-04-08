output "email" {
  description = "Email du service account"
  value       = google_service_account.this.email
}

output "name" {
  description = "Nom complet du service account"
  value       = google_service_account.this.name
}
