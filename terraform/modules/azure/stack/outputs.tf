output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "instance_ids" {
  value = azurerm_linux_virtual_machine.this[*].id
}
