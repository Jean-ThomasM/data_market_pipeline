variable "project_id" {
  description = "ID du projet GCP"
  type        = string
}

variable "region" {
  description = "Région GCP du workflow"
  type        = string
}

variable "name" {
  description = "Nom du workflow"
  type        = string
}

variable "description" {
  description = "Description du workflow"
  type        = string
  default     = null
}

variable "service_account_email" {
  description = "Service account utilisé à l'exécution du workflow"
  type        = string
}

variable "source_contents" {
  description = "Contenu YAML du workflow"
  type        = string
}
