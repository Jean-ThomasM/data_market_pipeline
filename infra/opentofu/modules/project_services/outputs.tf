output "enabled_services" {
  description = "Services activés sur le projet"
  value       = keys(google_project_service.this)
}