provider "google" {
  region = var.region
}

variable "region" {
  type = string
}

module "stack" {
  source = "../../terraform/modules/gcp/stack"

  region = var.region
}

output "provider" {
  value = "gcp"
}

output "instance_ids" {
  value = module.stack.instance_ids
}
