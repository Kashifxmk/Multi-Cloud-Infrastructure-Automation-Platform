provider "azurerm" {
  features {}
}

variable "region" { type = string }

output "provider" { value = "azure" }
