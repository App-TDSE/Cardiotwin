output "public_ip_address" {
  description = "Dirección IP pública del servidor CardioTwin. Accede a través de http://<IP> en tu navegador."
  value       = azurerm_linux_virtual_machine.vm.public_ip_address
}
