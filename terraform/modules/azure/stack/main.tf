resource "azurerm_resource_group" "this" {
  name     = var.project_name
  location = var.region
}

resource "azurerm_virtual_network" "this" {
  name                = "${var.project_name}-network"
  address_space       = [var.vpc_cidr]
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
}

resource "azurerm_subnet" "private" {
  name                 = "${var.project_name}-private"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [cidrsubnet(var.vpc_cidr, 8, 1)]
}

resource "azurerm_network_interface" "this" {
  count               = var.vm_count
  name                = "${var.project_name}-nic-${count.index + 1}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.private.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_linux_virtual_machine" "this" {
  count                           = var.vm_count
  name                            = "${var.project_name}-${count.index + 1}"
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  size                            = var.machine_type
  admin_username                  = "cloudpilot"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.this[count.index].id]

  admin_ssh_key {
    username   = "cloudpilot"
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = var.image_publisher
    offer     = var.image_offer
    sku       = var.image_sku
    version   = "latest"
  }
}
