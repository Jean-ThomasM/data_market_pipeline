variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  description = "Cloud Run region"
}

variable "job_name" {
  type        = string
  description = "Name of the Cloud Run Job"
}

variable "image" {
  type        = string
  description = "Docker image URI"
}

variable "service_account_email" {
  type        = string
  description = "Service account used by the job"
}

variable "cpu" {
  type        = string
  default     = "1"
}

variable "memory" {
  type        = string
  default     = "512Mi"
}