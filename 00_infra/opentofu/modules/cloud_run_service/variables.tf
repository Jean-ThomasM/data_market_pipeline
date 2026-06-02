variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name"
}

variable "image" {
  type        = string
  description = "Container image"
}

variable "service_account_email" {
  type        = string
  description = "Service account used by Cloud Run"
}

variable "port" {
  type        = number
  description = "Container port"
  default     = 5678
}

variable "cpu" {
  type        = string
  description = "CPU limit"
  default     = "1"
}

variable "memory" {
  type        = string
  description = "Memory limit"
  default     = "2Gi"
}

variable "env_vars" {
  type        = map(string)
  description = "Environment variables"
  default     = {}
}

variable "manual_instance_count" {
  type        = number
  description = "Fixed number of Cloud Run instances"
  default     = 1
}

variable "secret_env_vars" {
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

variable "cloud_sql_instances" {
  type    = list(string)
  default = []
}