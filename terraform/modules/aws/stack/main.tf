resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = var.project_name
  }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone = "${data.aws_region.current.name}a"

  tags = {
    Name = "${var.project_name}-private"
  }
}

data "aws_region" "current" {}

resource "aws_security_group" "internal" {
  name   = "${var.project_name}-internal"
  vpc_id = aws_vpc.this.id

  ingress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "this" {
  count                       = var.vm_count
  ami                         = var.ami_id
  instance_type               = var.machine_type
  subnet_id                   = aws_subnet.private.id
  vpc_security_group_ids      = [aws_security_group.internal.id]
  associate_public_ip_address = false

  tags = {
    Name = "${var.project_name}-${count.index + 1}"
  }
}
