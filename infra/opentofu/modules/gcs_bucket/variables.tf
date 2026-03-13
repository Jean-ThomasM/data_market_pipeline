variable "name" {
  description = "Nom du bucket GCS"
  type        = string
}

variable "location" {
  description = "Localisation du bucket"
  type        = string
}

variable "versioning_enabled" {
  description = "Active ou non le versioning"
  type        = bool
  default     = true
}