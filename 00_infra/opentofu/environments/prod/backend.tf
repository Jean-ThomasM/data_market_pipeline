terraform {
  backend "gcs" {
    bucket = "A_REMPLIR_PLUS_TARD"
    prefix = "opentofu/prod"
  }
}