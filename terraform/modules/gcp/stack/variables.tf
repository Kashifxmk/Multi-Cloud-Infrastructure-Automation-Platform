variable "project_name" {
  type    = string
  default = "cloudpilot"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "region" {
  type = string
}

variable "vm_count" {
  type    = number
  default = 1
}

variable "machine_type" {
  type    = string
  default = "e2-medium"
}

variable "boot_image" {
  type    = string
  default = "ubuntu-os-cloud/ubuntu-2204-lts"
}
