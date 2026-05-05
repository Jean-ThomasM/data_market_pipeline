terraform {
  backend "gcs" {
    bucket = "data-market-386959-data-lake-tofu-state-dev"
    prefix = "opentofu/dev"
  }
}