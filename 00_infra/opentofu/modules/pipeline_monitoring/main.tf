resource "google_monitoring_notification_channel" "email" {
  display_name = "Pipeline Alertes Email ${var.environment}"
  type         = "email"
  labels = {
    email_address = var.notification_email
  }
}

resource "google_monitoring_uptime_check_config" "n8n" {
  display_name = "n8n Health Check ${var.environment}"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/health"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      host = var.n8n_uptime_host
    }
  }
}

resource "google_logging_metric" "run_job_errors" {
  name   = "cloud_run_job_errors_${var.environment}"
  filter = "resource.type = \"cloud_run_job\" severity = ERROR"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "workflow_errors" {
  name   = "workflow_errors_${var.environment}"
  filter = "resource.type = \"workflows.googleapis.com/Workflow\" severity = ERROR"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "run_job_all" {
  name   = "cloud_run_job_all_${var.environment}"
  filter = "resource.type = \"cloud_run_job\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "n8n_errors" {
  name   = "n8n_errors_${var.environment}"
  filter = "resource.type = \"cloud_run_revision\" resource.labels.service_name = \"n8n-${var.environment}\" severity = ERROR"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_monitoring_alert_policy" "extract_job_failed" {
  display_name          = "Extracteur Cloud Run en échec - ${var.environment}"
  combiner              = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]

  conditions {
    display_name = "Au moins un job extracteur a généré des erreurs"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_job\" AND metric.type = \"logging.googleapis.com/user/${google_logging_metric.run_job_errors.name}\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_COUNT"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
}

resource "google_monitoring_alert_policy" "workflow_load_failed" {
  display_name          = "Chargement BigQuery en échec - ${var.environment}"
  combiner              = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]

  conditions {
    display_name = "Au moins un workflow de chargement a généré des erreurs"
    condition_threshold {
      filter          = "resource.type = \"workflows.googleapis.com/Workflow\" AND metric.type = \"logging.googleapis.com/user/${google_logging_metric.workflow_errors.name}\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_COUNT"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
}

resource "time_sleep" "n8n_metric_propagation" {
  depends_on = [
    google_logging_metric.run_job_errors,
    google_logging_metric.workflow_errors,
    google_logging_metric.run_job_all,
    google_logging_metric.n8n_errors,
  ]

  create_duration = "30s"
}

resource "google_monitoring_alert_policy" "n8n_down" {
  display_name          = "Erreurs n8n - ${var.environment}"
  combiner              = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]
  depends_on            = [time_sleep.n8n_metric_propagation]

  conditions {
    display_name = "Au moins une erreur dans les logs du service n8n"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"n8n-${var.environment}\" AND metric.type = \"logging.googleapis.com/user/${google_logging_metric.n8n_errors.name}\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_COUNT"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
}

resource "google_monitoring_alert_policy" "pipeline_stale" {
  display_name          = "Pipeline inactif depuis 24h - ${var.environment}"
  combiner              = "OR"
  notification_channels = [google_monitoring_notification_channel.email.id]

  conditions {
    display_name = "Aucune exécution de Cloud Run Job en 24h"
    condition_absent {
      filter   = "resource.type = \"cloud_run_job\" AND metric.type = \"logging.googleapis.com/user/${google_logging_metric.run_job_all.name}\""
      duration = "84600s"
      aggregations {
        alignment_period     = "3600s"
        per_series_aligner   = "ALIGN_COUNT"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
}

resource "google_monitoring_dashboard" "pipeline" {
  dashboard_json = templatefile("${path.module}/dashboards/pipeline_overview.json.tftpl", {
    environment = var.environment
    project_id  = var.project_id
  })
}
