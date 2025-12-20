#!/bin/bash
# =============================================================================
# Foundry Observability Demo - Quick Deployment Script
# =============================================================================
# This script automates the deployment of the Foundry Observability Demo
# infrastructure to Azure.
#
# Usage:
#   ./deploy.sh [environment-name]
#
# Example:
#   ./deploy.sh demo
#   ./deploy.sh prod
# =============================================================================

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-foundry-demo"
RESOURCE_GROUP_LOCATION="switzerlandnorth"
DEPLOYMENT_LOCATION="swedencentral"
ENVIRONMENT_NAME="${1:-demo}"
TEMPLATE_FILE="main.bicep"
PARAMETERS_FILE="parameters.json"
ARTIFACT_DIR=".local"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

log_info "Starting Foundry Observability Demo deployment..."
log_info "Environment: $ENVIRONMENT_NAME"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "Deployment Location: $DEPLOYMENT_LOCATION"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed. Please install it first."
    log_error "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

log_info "Azure CLI version: $(az version --query '"azure-cli"' -o tsv)"

# Check if logged in
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

ACCOUNT_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
log_info "Using subscription: $ACCOUNT_NAME ($SUBSCRIPTION_ID)"

# Ensure local artifact directory exists (ignored by git)
mkdir -p "$ARTIFACT_DIR"

ensure_role_assignment() {
    local scope=$1
    local role=$2
    local principal=$3

    if az role assignment list --scope "$scope" --role "$role" --assignee "$principal" --query "[0].id" -o tsv | grep -q "."; then
        log_info "Role '$role' already assigned to principal $principal at scope $scope"
    else
        log_info "Assigning role '$role' to principal $principal at scope $scope"
        az role assignment create \
            --assignee "$principal" \
            --role "$role" \
            --scope "$scope" \
            --only-show-errors >/dev/null
    fi
}

# =============================================================================
# Resource Group Setup
# =============================================================================

log_info "Checking if resource group '$RESOURCE_GROUP' exists..."
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    log_info "Resource group '$RESOURCE_GROUP' already exists."
else
    log_info "Creating resource group '$RESOURCE_GROUP' in $RESOURCE_GROUP_LOCATION..."
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$RESOURCE_GROUP_LOCATION"
    log_info "Resource group created successfully."
fi

# =============================================================================
# Validation (What-If)
# =============================================================================

log_info "Running deployment validation (what-if analysis)..."
az deployment group what-if \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "$PARAMETERS_FILE" \
    --parameters environmentName="$ENVIRONMENT_NAME" \
    --parameters deployerObjectId="$USER_OBJECT_ID"

echo ""
read -p "Do you want to proceed with the deployment? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_warn "Deployment cancelled by user."
    exit 0
fi

# =============================================================================
# Deployment
# =============================================================================

log_info "Starting infrastructure deployment..."
DEPLOYMENT_NAME="main-$(date +%Y%m%d-%H%M%S)"
DEPLOYMENT_RESULT_FILE="$ARTIFACT_DIR/deployment-result-$DEPLOYMENT_NAME.json"
DEPLOYMENT_OUTPUTS_FILE="$ARTIFACT_DIR/deployment-outputs-$DEPLOYMENT_NAME.json"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "$PARAMETERS_FILE" \
    --parameters environmentName="$ENVIRONMENT_NAME" \
    --parameters deployerObjectId="$USER_OBJECT_ID" \
    --output json > "$DEPLOYMENT_RESULT_FILE"

if [ $? -eq 0 ]; then
    log_info "Deployment completed successfully!"
else
    log_error "Deployment failed. Check the error messages above."
    exit 1
fi

# =============================================================================
# Extract Outputs
# =============================================================================

log_info "Extracting deployment outputs..."

az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs > "$DEPLOYMENT_OUTPUTS_FILE"

log_info "Deployment outputs saved to: $DEPLOYMENT_OUTPUTS_FILE"

# Extract key values
FUNCTION_APP_NAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query properties.outputs.functionAppName.value -o tsv)
STATIC_WEB_APP_NAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query properties.outputs.staticWebAppName.value -o tsv)
KEY_VAULT_NAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query properties.outputs.keyVaultName.value -o tsv)
SEARCH_SERVICE_NAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query properties.outputs.searchServiceName.value -o tsv)
STORAGE_ACCOUNT_NAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query properties.outputs.storageAccountName.value -o tsv)
KEY_VAULT_ID=$(az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" --query id -o tsv)

# Ensure the caller can set secrets in Key Vault before post-deployment writes
ensure_role_assignment "$KEY_VAULT_ID" "Key Vault Secrets Officer" "$USER_OBJECT_ID"

echo ""
log_info "==================================================================="
log_info "Deployment Summary"
log_info "==================================================================="
log_info "Function App:       $FUNCTION_APP_NAME"
log_info "Static Web App:     $STATIC_WEB_APP_NAME"
log_info "Key Vault:          $KEY_VAULT_NAME"
log_info "AI Search:          $SEARCH_SERVICE_NAME"
log_info "Storage Account:    $STORAGE_ACCOUNT_NAME"
log_info "==================================================================="

# =============================================================================
# Post-Deployment Tasks
# =============================================================================

echo ""
log_info "Running post-deployment configuration..."

# Store Azure Search Admin Key in Key Vault
log_info "Retrieving Azure AI Search admin key..."
SEARCH_ADMIN_KEY=$(az search admin-key show \
    --resource-group "$RESOURCE_GROUP" \
    --service-name "$SEARCH_SERVICE_NAME" \
    --query primaryKey -o tsv)

log_info "Storing Azure AI Search admin key in Key Vault..."
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "AzureSearchAdminKey" \
    --value "$SEARCH_ADMIN_KEY" \
    --output none

# Store Storage Account Key in Key Vault
log_info "Retrieving Storage Account key..."
STORAGE_KEY=$(az storage account keys list \
    --resource-group "$RESOURCE_GROUP" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --query '[0].value' -o tsv)

log_info "Storing Storage Account key in Key Vault..."
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "StorageAccountKey" \
    --value "$STORAGE_KEY" \
    --output none

# Store connection strings for App Service Key Vault references
log_info "Storing AzureWebJobsStorage connection string in Key Vault..."
AZURE_WEBJOBS_STORAGE_CONN="DefaultEndpointsProtocol=https;AccountName=${STORAGE_ACCOUNT_NAME};AccountKey=${STORAGE_KEY};EndpointSuffix=core.windows.net"
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "AzureWebJobsStorage" \
    --value "$AZURE_WEBJOBS_STORAGE_CONN" \
    --output none

log_info "Storing WEBSITE_CONTENTAZUREFILECONNECTIONSTRING in Key Vault..."
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "WebsiteContentAzureFileConnectionString" \
    --value "$AZURE_WEBJOBS_STORAGE_CONN" \
    --output none

log_info "Post-deployment configuration completed!"

# =============================================================================
# Next Steps
# =============================================================================

echo ""
log_info "==================================================================="
log_info "Deployment Complete!"
log_info "==================================================================="
echo ""
log_info "Next steps:"
echo "  1. Review deployment outputs in: $DEPLOYMENT_OUTPUTS_FILE"
echo "  2. Configure Static Web App deployment token in GitHub Secrets"
echo "  3. Deploy Function App code (Issue #7)"
echo "  4. Deploy Static Web App code (Issue #3)"
echo ""
log_info "For detailed instructions, see: infra/README.md"
echo ""

log_info "Deployment script completed successfully!"
