variable "project_id" {
  description = "ID du projet GCP"
  type        = string
}

variable "location" {
  description = "Région du repository Artifact Registry"
  type        = string
}

variable "repository_id" {
  description = "Nom du repository Artifact Registry"
  type        = string
}

variable "description" {
  description = "Description du repository"
  type        = string
  default     = "Docker images for data pipelines"
}