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