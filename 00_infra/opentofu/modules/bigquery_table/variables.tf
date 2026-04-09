variable "project_id" {
  description = "ID du projet GCP"
  type        = string
}

variable "dataset_id" {
  description = "ID du dataset BigQuery"
  type        = string
}

variable "table_id" {
  description = "ID de la table BigQuery"
  type        = string
}

variable "schema" {
  description = "Schema JSON de la table BigQuery"
  type        = string
}

variable "deletion_protection" {
  description = "Active la protection contre la suppression de la table"
  type        = bool
  default     = false
}
