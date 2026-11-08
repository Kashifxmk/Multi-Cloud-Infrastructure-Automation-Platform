resource "google_compute_network" "this" {
  name                    = var.project_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private" {
  name                     = "${var.project_name}-private"
  ip_cidr_range            = cidrsubnet(var.vpc_cidr, 8, 1)
  region                   = var.region
  network                  = google_compute_network.this.id
  private_ip_google_access = true
}

resource "google_compute_firewall" "internal" {
  name    = "${var.project_name}-internal"
  network = google_compute_network.this.name

  allow {
    protocol = "tcp"
  }

  source_ranges = [var.vpc_cidr]
}

resource "google_compute_instance" "this" {
  count        = var.vm_count
  name         = "${var.project_name}-${count.index + 1}"
  machine_type = var.machine_type
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = var.boot_image
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.private.id
  }
}
