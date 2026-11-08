provider "aws" {
  region = var.region
}

variable "region" {
  type = string
}

variable "ami_id" {
  type = string
}

module "stack" {
  source = "../../terraform/modules/aws/stack"

  ami_id = var.ami_id
}

output "provider" {
  value = "aws"
}

output "instance_ids" {
  value = module.stack.instance_ids
}
