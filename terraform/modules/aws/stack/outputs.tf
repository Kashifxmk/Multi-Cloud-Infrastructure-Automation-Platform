output "vpc_id" {
  value = aws_vpc.this.id
}

output "instance_ids" {
  value = aws_instance.this[*].id
}
