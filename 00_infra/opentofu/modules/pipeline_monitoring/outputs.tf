output "dashboard_id" {
  description = "Monitoring dashboard resource ID"
  value       = google_monitoring_dashboard.pipeline.id
}

output "alert_policy_names" {
  description = "List of alert policy display names"
  value = [
    google_monitoring_alert_policy.extract_job_failed.display_name,
    google_monitoring_alert_policy.workflow_load_failed.display_name,
    google_monitoring_alert_policy.n8n_down.display_name,
    google_monitoring_alert_policy.pipeline_stale.display_name,
  ]
}

output "notification_channel_name" {
  description = "Notification channel name"
  value       = google_monitoring_notification_channel.email.name
}
