variable "subscription_id" {
  description = "Azure subscription ID used for deployment."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name."
  type        = string
  default     = "rg-media-transcoder"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "name" {
  description = "Short globally unique application name prefix."
  type        = string
  default     = "media-transcoder"
}

variable "storage_account_name" {
  description = "Globally unique lowercase storage account name."
  type        = string
}

variable "registry_name" {
  description = "Globally unique lowercase Azure Container Registry name."
  type        = string
}

variable "container_image" {
  description = "Container image containing the API."
  type        = string
}
