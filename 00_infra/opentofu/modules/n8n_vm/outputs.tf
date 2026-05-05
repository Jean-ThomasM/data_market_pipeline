output "n8n_external_ip" {
  value = google_compute_instance.n8n_vm.network_interface[0].access_config[0].nat_ip
}