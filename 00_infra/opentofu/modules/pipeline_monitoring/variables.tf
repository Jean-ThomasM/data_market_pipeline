variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "notification_email" {
  description = "Email address for pipeline alerts"
  type        = string
}

variable "n8n_uptime_host" {
  description = "Hostname for the remote n8n uptime check"
  type        = string
}
