#!/bin/bash
# =============================================================================
# Generate .env file from Azure deployment outputs
# =============================================================================
# This script extracts deployment outputs and creates a .env file for local
# development.
#
# Usage:
#   ./scripts/generate-env.sh [deployment-name]
#
# Example:
#   ./scripts/generate-env.sh main
# =============================================================================

set -e

RESOURCE_GROUP="rg-foundry-demo"
DEPLOYMENT_NAME="${1:-main}"
ENV_FILE=".env"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo "Error: Not logged in to Azure. Run 'az login' first."
    exit 1
fi

log_info "Fetching deployment outputs from '$DEPLOYMENT_NAME'..."

# Get deployment outputs
OUTPUTS=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$OUTPUTS" ]; then
    echo "Error: Could not fetch deployment outputs"
    echo "Make sure the deployment '$DEPLOYMENT_NAME' exists in resource group '$RESOURCE_GROUP'"
    exit 1
fi

# Extract values
log_info "Extracting configuration values..."

APPINSIGHTS_NAME=$(echo "$OUTPUTS" | jq -r .applicationInsightsName.value)
STORAGE_NAME=$(echo "$OUTPUTS" | jq -r .storageAccountName.value)
STORAGE_ENDPOINT=$(echo "$OUTPUTS" | jq -r .storageBlobEndpoint.value)
SEARCH_ENDPOINT=$(echo "$OUTPUTS" | jq -r .searchServiceEndpoint.value)
SEARCH_NAME=$(echo "$OUTPUTS" | jq -r .searchServiceName.value)
KEYVAULT_URI=$(echo "$OUTPUTS" | jq -r .keyVaultUri.value)
KEYVAULT_NAME=$(echo "$OUTPUTS" | jq -r .keyVaultName.value)
FUNCTION_NAME=$(echo "$OUTPUTS" | jq -r .functionAppName.value)
FUNCTION_HOST=$(echo "$OUTPUTS" | jq -r .functionAppHostName.value)
STATIC_HOST=$(echo "$OUTPUTS" | jq -r .staticWebAppDefaultHostName.value)
STATIC_NAME=$(echo "$OUTPUTS" | jq -r .staticWebAppName.value)

# Foundry
FOUNDRY_ACCOUNT_ENDPOINT=$(echo "$OUTPUTS" | jq -r .foundryAccountEndpoint.value)
FOUNDRY_PROJECT_NAME=$(echo "$OUTPUTS" | jq -r .foundryProjectName.value)

# Fetch App Insights details without relying on deployment outputs (avoid persisting sensitive values)
log_info "Fetching Application Insights details from resource '$APPINSIGHTS_NAME'..."

APPINSIGHTS_CONNECTION=$(az resource show \
    --resource-group "$RESOURCE_GROUP" \
    --resource-type "Microsoft.Insights/components" \
    --name "$APPINSIGHTS_NAME" \
    --query properties.ConnectionString -o tsv 2>/dev/null || echo "")

APPINSIGHTS_KEY=$(az resource show \
    --resource-group "$RESOURCE_GROUP" \
    --resource-type "Microsoft.Insights/components" \
    --name "$APPINSIGHTS_NAME" \
    --query properties.InstrumentationKey -o tsv 2>/dev/null || echo "")

# Get secrets from Key Vault
log_info "Fetching secrets from Key Vault '$KEYVAULT_NAME'..."

SEARCH_ADMIN_KEY=$(az keyvault secret show \
    --vault-name "$KEYVAULT_NAME" \
    --name "AzureSearchAdminKey" \
    --query value -o tsv 2>/dev/null || echo "")

STORAGE_KEY=$(az keyvault secret show \
    --vault-name "$KEYVAULT_NAME" \
    --name "StorageAccountKey" \
    --query value -o tsv 2>/dev/null || echo "")

# Backup existing .env if it exists
if [ -f "$ENV_FILE" ]; then
    log_warn "Backing up existing $ENV_FILE to ${ENV_FILE}.backup"
    cp "$ENV_FILE" "${ENV_FILE}.backup"
fi

# Create .env file
log_info "Creating $ENV_FILE..."

cat > "$ENV_FILE" << EOF
# =============================================================================
# Foundry Observability Demo - Environment Variables
# =============================================================================
# Auto-generated on $(date)
# Deployment: $DEPLOYMENT_NAME
# Resource Group: $RESOURCE_GROUP
# =============================================================================

# Azure Resource Group
RESOURCE_GROUP_NAME=$RESOURCE_GROUP

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=$APPINSIGHTS_CONNECTION
APPINSIGHTS_INSTRUMENTATIONKEY=$APPINSIGHTS_KEY

# Azure Storage
STORAGE_ACCOUNT_NAME=$STORAGE_NAME
STORAGE_ACCOUNT_KEY=$STORAGE_KEY
STORAGE_BLOB_ENDPOINT=$STORAGE_ENDPOINT

# Azure AI Search
AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
AZURE_SEARCH_ADMIN_KEY=$SEARCH_ADMIN_KEY
AZURE_SEARCH_SERVICE_NAME=$SEARCH_NAME

# Azure Key Vault
AZURE_KEY_VAULT_ENDPOINT=$KEYVAULT_URI
KEY_VAULT_NAME=$KEYVAULT_NAME

# Azure Function App
AZURE_FUNCTION_APP_URL=https://$FUNCTION_HOST
FUNCTION_APP_NAME=$FUNCTION_NAME

# Static Web App
STATIC_WEB_APP_URL=https://$STATIC_HOST
STATIC_WEB_APP_NAME=$STATIC_NAME

# Azure Functions Runtime (for local development)
AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=$STORAGE_NAME;AccountKey=$STORAGE_KEY;EndpointSuffix=core.windows.net
WEBSITE_CONTENTAZUREFILECONNECTIONSTRING=DefaultEndpointsProtocol=https;AccountName=$STORAGE_NAME;AccountKey=$STORAGE_KEY;EndpointSuffix=core.windows.net
WEBSITE_CONTENTSHARE=$(echo "$FUNCTION_NAME" | tr '[:upper:]' '[:lower:]')
FUNCTIONS_EXTENSION_VERSION=~4
FUNCTIONS_WORKER_RUNTIME=python

# Azure AI Foundry
FOUNDRY_ACCOUNT_ENDPOINT=$FOUNDRY_ACCOUNT_ENDPOINT
FOUNDRY_PROJECT_NAME=$FOUNDRY_PROJECT_NAME

# Development Settings
ENVIRONMENT=local
DEBUG=true
LOG_LEVEL=INFO
EOF

log_info "Successfully created $ENV_FILE"

# Check for missing values
if [ -z "$SEARCH_ADMIN_KEY" ]; then
    log_warn "Azure Search admin key not found in Key Vault"
    log_warn "Run: az keyvault secret show --vault-name $KEYVAULT_NAME --name AzureSearchAdminKey"
fi

if [ -z "$STORAGE_KEY" ]; then
    log_warn "Storage account key not found in Key Vault"
    log_warn "Run: az keyvault secret show --vault-name $KEYVAULT_NAME --name StorageAccountKey"
fi

echo ""
log_info "==================================================================="
log_info "Manual steps remaining:"
log_info "==================================================================="
echo "1. Configure Static Web App deployment token in GitHub Secrets (for CI/CD)"
echo ""
log_info "Your .env file is ready for local development!"
