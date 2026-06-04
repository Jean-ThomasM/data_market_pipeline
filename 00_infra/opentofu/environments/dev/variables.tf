variable "project_id" {
  description = "ID du projet GCP"
  type        = string
}

variable "region" {
  description = "Région GCP par défaut"
  type        = string
}

variable "environment" {
  description = "Nom de l'environnement"
  type        = string
}

variable "bucket_location" {
  description = "Localisation du bucket GCS"
  type        = string
}

variable "bigquery_location" {
  description = "Localisation des datasets BigQuery"
  type        = string
}

variable "github_repo" {
  description = "Dépôt GitHub au format 'owner/repo' pour la fédération d'identité WIF"
  type        = string
}

variable "monitoring_email" {
  description = "Email de réception des alertes pipeline"
  type        = string
}

variable "n8n_host" {
  description = "Hostname public du n8n distant"
  type        = string
}
