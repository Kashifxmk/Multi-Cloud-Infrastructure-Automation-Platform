output "network_id" {
  value = google_compute_network.this.id
}

output "instance_ids" {
  value = google_compute_instance.this[*].id
}
