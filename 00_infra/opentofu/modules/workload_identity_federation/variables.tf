variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "project_number" {
  description = "GCP project number (numeric, used in provider resource name)"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository in 'owner/repo' format (e.g. 'Jean-ThomasM/data_market_pipeline')"
  type        = string
}

variable "service_account_email" {
  description = "Email of the service account to allow GitHub to impersonate"
  type        = string
}
