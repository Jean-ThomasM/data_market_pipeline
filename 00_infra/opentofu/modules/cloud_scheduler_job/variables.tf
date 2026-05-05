variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  description = "Scheduler and Cloud Run region"
}

variable "scheduler_name" {
  type        = string
  description = "Cloud Scheduler job name"
}

variable "schedule" {
  type        = string
  description = "Cron schedule"
}

variable "time_zone" {
  type        = string
  description = "Scheduler timezone"
  default     = "Europe/Paris"
}

variable "cloud_run_job_name" {
  type        = string
  description = "Cloud Run Job to execute"
}

variable "scheduler_service_account_email" {
  type        = string
  description = "Service account used by Cloud Scheduler"
}
