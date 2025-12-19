// =============================================================================
// Foundry Observability Demo - Infrastructure as Code
// =============================================================================
// This Bicep template deploys the minimal demo infrastructure for the
// Foundry observability demo project.
//
// Target Resource Group: rg-foundry-demo (located in Switzerland North)
// All resources deployed in: Sweden Central
//
// Resources:
// - Static Web App
// - Function App (Linux Consumption)
// - Application Insights + Log Analytics Workspace
// - Azure AI Search (Basic tier)
// - Storage Account
// - Key Vault
// =============================================================================

@description('The location for all resources (except Resource Group)')
param location string = 'swedencentral'

@description('The location for Static Web App (must be in supported region)')
param staticWebAppLocation string = 'westeurope'

@description('The environment name (e.g., dev, test, prod)')
param environmentName string = 'demo'

@description('The unique suffix for resource names to ensure uniqueness')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('The name of the Static Web App')
param staticWebAppName string = 'swa-foundry-${environmentName}-${uniqueSuffix}'

@description('The name of the Function App')
param functionAppName string = 'func-foundry-${environmentName}-${uniqueSuffix}'

@description('The name of the Storage Account')
param storageAccountName string = 'stfoundry${environmentName}${take(uniqueSuffix, 8)}'

@description('The name of the Log Analytics Workspace')
param logAnalyticsWorkspaceName string = 'log-foundry-${environmentName}-${uniqueSuffix}'

@description('The name of the Application Insights')
param appInsightsName string = 'appi-foundry-${environmentName}-${uniqueSuffix}'

@description('The name of the Azure AI Search service')
param searchServiceName string = 'srch-foundry-${environmentName}-${uniqueSuffix}'

@description('The name of the Key Vault')
param keyVaultName string = 'kv-foundry-${take(uniqueSuffix, 12)}'

@description('The SKU of the Azure AI Search service')
@allowed([
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param searchServiceSku string = 'basic'

@description('The SKU of the Function App hosting plan')
param functionAppSku string = 'Y1'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environmentName
  Project: 'FoundryObservabilityDemo'
  ManagedBy: 'Bicep'
}

// =============================================================================
// Storage Account
// =============================================================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Blob Services for the storage account
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

// Container for function app
resource functionAppContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobServices
  name: 'function-releases'
  properties: {
    publicAccess: 'None'
  }
}

// =============================================================================
// Log Analytics Workspace
// =============================================================================
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// =============================================================================
// Application Insights
// =============================================================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    RetentionInDays: 30
    IngestionMode: 'LogAnalytics'
  }
}

// =============================================================================
// Azure AI Search
// =============================================================================
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: searchServiceSku
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
    }
  }
}

// =============================================================================
// Key Vault
// =============================================================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// =============================================================================
// App Service Plan (Consumption)
// =============================================================================
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: 'asp-${functionAppName}'
  location: location
  tags: tags
  sku: {
    name: functionAppSku
    tier: 'Dynamic'
  }
  kind: 'functionapp'
  properties: {
    reserved: true // Linux
  }
}

// =============================================================================
// Function App
// =============================================================================
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'AZURE_SEARCH_ENDPOINT'
          value: 'https://${searchService.name}.search.windows.net'
        }
        {
          name: 'AZURE_KEY_VAULT_ENDPOINT'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'STORAGE_ACCOUNT_NAME'
          value: storageAccount.name
        }
      ]
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
  }
}

// =============================================================================
// Static Web App
// =============================================================================
resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: staticWebAppName
  location: staticWebAppLocation
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    buildProperties: {
      skipGithubActionWorkflowGeneration: true
    }
  }
}

// Link Static Web App to App Insights
resource staticWebAppAppInsights 'Microsoft.Web/staticSites/config@2023-01-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  }
}

// =============================================================================
// Role Assignments
// =============================================================================

// Grant Function App access to Key Vault Secrets
resource keyVaultSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Function App access to Storage Blob Data Contributor
resource storageBlobDataContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, 'Storage Blob Data Contributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The name of the resource group')
output resourceGroupName string = resourceGroup().name

@description('The location of the deployed resources')
output location string = location

// Storage Account Outputs
@description('The name of the storage account')
output storageAccountName string = storageAccount.name

@description('The primary endpoint for blob storage')
output storageBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob

// Application Insights Outputs
@description('The Application Insights connection string')
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString

@description('The Application Insights instrumentation key')
output applicationInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey

@description('The name of the Application Insights resource')
output applicationInsightsName string = appInsights.name

// Log Analytics Outputs
@description('The Log Analytics Workspace ID')
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id

@description('The name of the Log Analytics Workspace')
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name

// Azure AI Search Outputs
@description('The Azure AI Search service endpoint')
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'

@description('The name of the Azure AI Search service')
output searchServiceName string = searchService.name

// Key Vault Outputs
@description('The Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('The name of the Key Vault')
output keyVaultName string = keyVault.name

// Function App Outputs
@description('The name of the Function App')
output functionAppName string = functionApp.name

@description('The default hostname of the Function App')
output functionAppHostName string = functionApp.properties.defaultHostName

@description('The Function App principal ID (for role assignments)')
output functionAppPrincipalId string = functionApp.identity.principalId

// Static Web App Outputs
@description('The name of the Static Web App')
output staticWebAppName string = staticWebApp.name

@description('The default hostname of the Static Web App')
output staticWebAppDefaultHostName string = staticWebApp.properties.defaultHostname

// App Settings for Function App (for use in issues #3 and #7)
// NOTE: AzureWebJobsStorage and WEBSITE_CONTENTAZUREFILECONNECTIONSTRING connection strings
// are incomplete and require AccountKey to be added. Retrieve the storage key from Key Vault
// and append ";AccountKey=<key>" to these connection strings for production use.
@description('Complete app settings for Function App configuration. Storage connection strings require AccountKey from Key Vault.')
output functionAppSettings object = {
  AzureWebJobsStorage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage}'
  WEBSITE_CONTENTAZUREFILECONNECTIONSTRING: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage}'
  WEBSITE_CONTENTSHARE: toLower(functionAppName)
  FUNCTIONS_EXTENSION_VERSION: '~4'
  FUNCTIONS_WORKER_RUNTIME: 'python'
  APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  APPINSIGHTS_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
  AZURE_SEARCH_ENDPOINT: 'https://${searchService.name}.search.windows.net'
  AZURE_KEY_VAULT_ENDPOINT: keyVault.properties.vaultUri
  STORAGE_ACCOUNT_NAME: storageAccount.name
}

// App Settings for Static Web App (for use in issues #3 and #7)
@description('Complete app settings for Static Web App configuration')
output staticWebAppSettings object = {
  APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  AZURE_FUNCTION_APP_URL: 'https://${functionApp.properties.defaultHostName}'
}
