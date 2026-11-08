provider "azurerm" {
  features {}
}

variable "region" {
  type = string
}

variable "ssh_public_key" {
  type = string
}

module "stack" {
  source = "../../terraform/modules/azure/stack"

  region         = var.region
  ssh_public_key = var.ssh_public_key
}

output "provider" {
  value = "azure"
}

output "instance_ids" {
  value = module.stack.instance_ids
}
