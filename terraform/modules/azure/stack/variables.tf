variable "project_name" {
  type    = string
  default = "cloudpilot"
}

variable "region" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "vm_count" {
  type    = number
  default = 1
}

variable "machine_type" {
  type    = string
  default = "Standard_B1s"
}

variable "ssh_public_key" {
  type = string
}

variable "image_publisher" {
  type    = string
  default = "Canonical"
}

variable "image_offer" {
  type    = string
  default = "0001-com-ubuntu-server-jammy"
}

variable "image_sku" {
  type    = string
  default = "22_04-lts-gen2"
}
