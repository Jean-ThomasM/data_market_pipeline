resource "google_cloud_run_v2_job" "this" {
  name     = var.job_name
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = var.service_account_email

      containers {
        image = var.image

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
}