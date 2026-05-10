variable "resource_group_name" {
  type        = string
  description = "Nombre del Resource Group en Azure"
  default     = "rg-cardiotwin"
}

variable "location" {
  type        = string
  description = "Región de Azure donde se desplegarán los recursos"
  default     = "southcentralus"
}

variable "vm_size" {
  type        = string
  description = "Tamaño de la máquina virtual"
  default     = "Standard_D2s_v3"
}

variable "admin_username" {
  type        = string
  description = "Usuario administrador de la máquina virtual"
  default     = "azureuser"
}
