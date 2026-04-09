terraform {
  backend "gcs" {
    bucket = "data-market-386959-opentofu-state"
    prefix = "dev"
  }
}