provider "aws" {
  region = var.region
}

variable "region" { type = string }

output "provider" { value = "aws" }
