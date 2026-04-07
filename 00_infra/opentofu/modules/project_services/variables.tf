variable "project_id" {
  description = "ID du projet GCP"
  type        = string
}

variable "services" {
  description = "Liste des APIs GCP à activer"
  type        = list(string)
}