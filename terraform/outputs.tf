output "api_url" {
  value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "storage_account_name" {
  value = azurerm_storage_account.media.name
}

output "registry_name" {
  value = azurerm_container_registry.this.name
}

output "registry_login_server" {
  value = azurerm_container_registry.this.login_server
}
