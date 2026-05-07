resource "google_cloud_run_v2_service" "this" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  scaling {
    scaling_mode          = "MANUAL"
    manual_instance_count = var.manual_instance_count
  }

  template {
    service_account = var.service_account_email

    annotations = merge(
      {
        "run.googleapis.com/cpu-throttling" = "false"
      },
      length(var.cloud_sql_instances) > 0 ? {
        "run.googleapis.com/cloudsql-instances" = join(",", var.cloud_sql_instances)
      } : {}
    )

    containers {
      image = var.image

      ports {
        container_port = var.port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      dynamic "env" {
  for_each = var.secret_env_vars

      content {
        name = env.key

        value_source {
          secret_key_ref {
            secret  = env.value.secret
            version = env.value.version
          }
        }
      }
    }
    }
  }
}