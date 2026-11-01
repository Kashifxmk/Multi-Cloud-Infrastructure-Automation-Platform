provider "google" {
  region = var.region
}

variable "region" { type = string }

output "provider" { value = "gcp" }
