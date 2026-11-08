variable "project_name" {
  type    = string
  default = "cloudpilot"
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
  default = "t3.micro"
}

variable "ami_id" {
  type = string
}
