terraform {
  required_version = ">= 1.6.0"

  backend "azurerm" {}

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_storage_account" "media" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
}

resource "azurerm_storage_container" "inputs" {
  name                  = "inputs"
  storage_account_id    = azurerm_storage_account.media.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "outputs" {
  name                  = "outputs"
  storage_account_id    = azurerm_storage_account.media.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "status" {
  name                  = "status"
  storage_account_id    = azurerm_storage_account.media.id
  container_access_type = "private"
}

resource "azurerm_storage_queue" "jobs" {
  name                 = "transcode-jobs"
  storage_account_name = azurerm_storage_account.media.name
}

resource "azurerm_container_registry" "this" {
  name                = var.registry_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "${var.name}-logs"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "this" {
  name                       = "${var.name}-env"
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
}

resource "azurerm_container_app" "api" {
  name                         = "${var.name}-api"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.this.login_server
    identity = "system"
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.media.primary_connection_string
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "api"
      image  = var.container_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

resource "azurerm_container_app" "worker" {
  name                         = "${var.name}-worker"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.this.login_server
    identity = "system"
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.media.primary_connection_string
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name    = "worker"
      image   = var.container_image
      command = ["python", "-m", "app.worker"]
      cpu     = 1.0
      memory  = "2Gi"

      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }
    }
  }
}

resource "azurerm_role_assignment" "api_acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.api.identity[0].principal_id
}

resource "azurerm_role_assignment" "worker_acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.worker.identity[0].principal_id
}
