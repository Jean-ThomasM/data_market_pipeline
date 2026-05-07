resource "google_sql_database_instance" "this" {
  name             = var.instance_name
  project          = var.project_id
  region           = var.region
  database_version = "POSTGRES_16"

  settings {
    tier = "db-f1-micro"
    edition = "ENTERPRISE"

    availability_type = "ZONAL"

    disk_type       = "PD_HDD"
    disk_size       = 10
    disk_autoresize = true

    backup_configuration {
      enabled = true
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "this" {
  name     = var.database_name
  project  = var.project_id
  instance = google_sql_database_instance.this.name
}

resource "google_sql_user" "this" {
  name     = var.database_user
  project  = var.project_id
  instance = google_sql_database_instance.this.name
  password = var.database_password
}
