resource "google_compute_instance" "n8n_vm" {
  name         = var.instance_name
  machine_type = "e2-medium"
  zone         = var.zone

  tags = ["n8n"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 20
    }
  }

  network_interface {
    network = "default"

    access_config {} # IP publique
  }


  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io

    systemctl start docker
    systemctl enable docker

    docker run -d \
      --name n8n \
      -p 80:5678 \
      -v n8n_data:/home/node/.n8n \
      n8nio/n8n
  EOF
}

resource "google_compute_firewall" "n8n_allow_http" {
  name    = "allow-n8n-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  target_tags = ["n8n"]

  source_ranges = ["0.0.0.0/0"]
}