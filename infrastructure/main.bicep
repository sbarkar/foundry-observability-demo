// Main Bicep template for Foundry Observability Demo
targetScope = 'subscription'

@description('Name of the resource group')
param resourceGroupName string = 'rg-foundry-demo'

@description('Location for all resources')
param location string = 'eastus'

@description('Name of the Azure OpenAI service')
param openAIServiceName string

@description('Name of the AI Search service')
param searchServiceName string

@description('Name of the Static Web App')
param staticWebAppName string

@description('Name of the Function App')
param functionAppName string

@description('Name of the Application Insights')
param appInsightsName string

@description('Entra ID Tenant ID')
param tenantId string

@description('Entra ID Client ID for authentication')
param clientId string

// Create resource group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
}

// Deploy resources into the resource group
module resources 'resources.bicep' = {
  scope: rg
  name: 'resources-deployment'
  params: {
    location: location
    openAIServiceName: openAIServiceName
    searchServiceName: searchServiceName
    staticWebAppName: staticWebAppName
    functionAppName: functionAppName
    appInsightsName: appInsightsName
    tenantId: tenantId
    clientId: clientId
  }
}

output resourceGroupName string = rg.name
output staticWebAppUrl string = resources.outputs.staticWebAppUrl
output functionAppUrl string = resources.outputs.functionAppUrl
output appInsightsConnectionString string = resources.outputs.appInsightsConnectionString
output appInsightsInstrumentationKey string = resources.outputs.appInsightsInstrumentationKey
