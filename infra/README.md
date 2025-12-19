# Foundry Observability Demo - Infrastructure Deployment

This directory contains the Infrastructure as Code (IaC) for deploying the Foundry Observability Demo to Azure.

## Overview

The Bicep template deploys a complete observability infrastructure in Azure, targeting the `rg-foundry-demo` resource group (Switzerland North), with all resources deployed in **Sweden Central**.

### Deployed Resources

| Resource Type | Purpose | SKU/Tier |
|--------------|---------|----------|
| **Static Web App** | Frontend hosting | Free |
| **Function App** | Backend API (Linux Consumption) | Y1 (Consumption) |
| **Storage Account** | Function App storage and data | Standard_LRS |
| **Application Insights** | Application monitoring and logging | Standard |
| **Log Analytics Workspace** | Centralized log storage | PerGB2018 |
| **Azure AI Search** | Search service for AI workloads | Basic |
| **Key Vault** | Secrets management | Standard |

### Architecture Notes

- **Function App**: Python 3.11 on Linux Consumption plan
- **Identity**: Function App uses System-Assigned Managed Identity
- **RBAC**: Function App has:
  - Key Vault Secrets User role on Key Vault
  - Storage Blob Data Contributor role on Storage Account
- **Security**: All resources use HTTPS only, TLS 1.2 minimum
- **Monitoring**: All compute resources connected to Application Insights

## Prerequisites

Before deploying, ensure you have:

1. **Azure CLI** installed and authenticated
   ```bash
   az --version
   az login
   az account show
   ```

2. **Correct subscription** selected
   ```bash
   az account set --subscription "<your-subscription-id>"
   ```

3. **Resource Group** `rg-foundry-demo` exists in Switzerland North
   ```bash
   az group create --name rg-foundry-demo --location switzerlandnorth
   ```

4. **Permissions**: You need Owner or Contributor + User Access Administrator roles on the resource group to assign RBAC roles

## Deployment Instructions

### Option 1: Deploy with Default Parameters

```bash
# From the repository root
cd infra

# Deploy using the parameters file
az deployment group create \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json
```

### Option 2: Deploy with Custom Parameters

You can override parameters at deployment time:

```bash
az deployment group create \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json \
  --parameters environmentName=prod \
  --parameters searchServiceSku=standard
```

### Option 3: Deploy with What-If Analysis (Recommended)

Preview changes before deployment:

```bash
az deployment group what-if \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json
```

Then deploy:

```bash
az deployment group create \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json
```

## Deployment Outputs

After successful deployment, the template outputs critical configuration values needed by downstream applications (issues #3 and #7).

### Retrieve All Outputs

```bash
az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs
```

### Key Outputs

The deployment provides:

#### For Function App Configuration (#7)
- `functionAppSettings`: Complete app settings object
- `applicationInsightsConnectionString`: Monitoring connection string
- `searchServiceEndpoint`: Azure AI Search endpoint
- `keyVaultUri`: Key Vault URI
- `storageAccountName`: Storage account name

#### For Static Web App Configuration (#3)
- `staticWebAppSettings`: Complete app settings object
- `staticWebAppDefaultHostName`: Web app URL
- `functionAppHostName`: Backend API URL

### Export Outputs to File

```bash
# Export all outputs as JSON
az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs > deployment-outputs.json

# Extract specific values
az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs.applicationInsightsConnectionString.value -o tsv
```

## Post-Deployment Configuration

### 1. Azure AI Search - Admin Key

The Azure AI Search admin key is not exposed via outputs (security best practice). Retrieve it manually:

```bash
SEARCH_SERVICE_NAME=$(az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs.searchServiceName.value -o tsv)

az search admin-key show \
  --resource-group rg-foundry-demo \
  --service-name $SEARCH_SERVICE_NAME
```

**Store the admin key in Key Vault:**

```bash
KEY_VAULT_NAME=$(az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs.keyVaultName.value -o tsv)

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "AzureSearchAdminKey" \
  --value "<admin-key-from-previous-command>"
```

### 2. Storage Account - Access Key

Similarly, retrieve and store the storage account key:

```bash
STORAGE_ACCOUNT_NAME=$(az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs.storageAccountName.value -o tsv)

STORAGE_KEY=$(az storage account keys list \
  --resource-group rg-foundry-demo \
  --account-name $STORAGE_ACCOUNT_NAME \
  --query '[0].value' -o tsv)

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "StorageAccountKey" \
  --value "$STORAGE_KEY"
```

### 3. Static Web App - Deployment Token

Retrieve the deployment token for CI/CD:

```bash
STATIC_WEB_APP_NAME=$(az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs.staticWebAppName.value -o tsv)

az staticwebapp secrets list \
  --name $STATIC_WEB_APP_NAME \
  --resource-group rg-foundry-demo \
  --query properties.apiKey -o tsv
```

**Store in GitHub Secrets** (not in Key Vault, as it's used by GitHub Actions):
- Go to your GitHub repository settings
- Navigate to Secrets and variables > Actions
- Add a new secret: `AZURE_STATIC_WEB_APPS_API_TOKEN`

## Manual Steps Required

### Microsoft Foundry Project Creation

**Important**: Foundry projects cannot be easily created via Bicep/IaC as they are in preview and don't have stable ARM/Bicep providers yet.

**Manual Steps**:

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com
   - Search for "Microsoft Foundry" or access via Azure AI Studio

2. **Create a Foundry Project**
   - Click "Create" or "New Project"
   - **Project Name**: `foundry-observability-demo`
   - **Resource Group**: Select `rg-foundry-demo`
   - **Location**: Select `Sweden Central`
   - **Associate with deployed resources**:
     - Link the Application Insights instance created by this deployment
     - Link the Storage Account for data storage
     - Link the Azure AI Search service for vector search capabilities

3. **Configure Project Settings**
   - Enable logging and monitoring
   - Set up any required connections to the Function App
   - Configure access policies as needed

4. **Note the Foundry Project Details**
   - Copy the Project ID/Endpoint
   - Store any required connection strings or keys in the Key Vault:
     ```bash
     az keyvault secret set \
       --vault-name $KEY_VAULT_NAME \
       --name "FoundryProjectEndpoint" \
       --value "<your-foundry-project-endpoint>"
     ```

### Alternative: Azure CLI (if available)

If Foundry supports CLI commands (check latest docs):

```bash
# Example command structure (verify with latest Foundry docs)
az foundry project create \
  --name foundry-observability-demo \
  --resource-group rg-foundry-demo \
  --location swedencentral \
  --app-insights $(az deployment group show --resource-group rg-foundry-demo --name main --query properties.outputs.applicationInsightsName.value -o tsv)
```

## Validation

### Verify Resources

```bash
# List all resources in the resource group
az resource list \
  --resource-group rg-foundry-demo \
  --output table

# Check Function App status
az functionapp show \
  --name $(az deployment group show --resource-group rg-foundry-demo --name main --query properties.outputs.functionAppName.value -o tsv) \
  --resource-group rg-foundry-demo \
  --query state
```

### Test Function App

```bash
FUNCTION_APP_URL="https://$(az deployment group show --resource-group rg-foundry-demo --name main --query properties.outputs.functionAppHostName.value -o tsv)"

# Should return 200 OK (once function code is deployed)
curl -I $FUNCTION_APP_URL
```

### Test Static Web App

```bash
STATIC_WEB_APP_URL="https://$(az deployment group show --resource-group rg-foundry-demo --name main --query properties.outputs.staticWebAppDefaultHostName.value -o tsv)"

# Should return 200 OK (once static content is deployed)
curl -I $STATIC_WEB_APP_URL
```

## Updating the Deployment

To update resources, modify `main.bicep` or `parameters.json` and redeploy:

```bash
az deployment group create \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json \
  --mode Incremental
```

**Note**: Incremental mode (default) only adds or updates resources. Use `--mode Complete` with caution as it will delete resources not defined in the template.

## Troubleshooting

### Deployment Fails with RBAC Error

If role assignments fail, ensure you have sufficient permissions:

```bash
# Check your role assignments
az role assignment list \
  --assignee $(az account show --query user.name -o tsv) \
  --resource-group rg-foundry-demo \
  --output table
```

You need either:
- Owner role on the resource group, OR
- Contributor + User Access Administrator roles

### Function App Not Starting

Check the Function App logs:

```bash
az functionapp log tail \
  --name $(az deployment group show --resource-group rg-foundry-demo --name main --query properties.outputs.functionAppName.value -o tsv) \
  --resource-group rg-foundry-demo
```

### Key Vault Access Issues

Verify the Function App's managed identity has access:

```bash
az role assignment list \
  --assignee $(az deployment group show --resource-group rg-foundry-demo --name main --query properties.outputs.functionAppPrincipalId.value -o tsv) \
  --scope $(az keyvault show --name $KEY_VAULT_NAME --query id -o tsv) \
  --output table
```

## Cleanup

To delete all deployed resources:

```bash
# Option 1: Delete the entire resource group
az group delete --name rg-foundry-demo --yes --no-wait

# Option 2: Delete specific resources (keeps RG)
az deployment group delete \
  --resource-group rg-foundry-demo \
  --name main

# Manually delete resources
az resource list --resource-group rg-foundry-demo --query '[].id' -o tsv | \
  xargs -I {} az resource delete --ids {}
```

**Warning**: Key Vault has soft-delete enabled (90 days). To permanently delete:

```bash
az keyvault purge --name $KEY_VAULT_NAME
```

## Security Best Practices

1. **Never commit secrets**: The template uses Key Vault references and managed identities
2. **RBAC over access keys**: Use managed identities where possible
3. **Least privilege**: Grant only necessary permissions
4. **Audit logs**: Enable diagnostic settings on Key Vault and other resources
5. **Network security**: Consider adding virtual network integration for production

## Parameters Reference

| Parameter | Description | Default | Allowed Values |
|-----------|-------------|---------|----------------|
| `location` | Deployment location | `swedencentral` | Any Azure region |
| `environmentName` | Environment name | `demo` | Any string |
| `uniqueSuffix` | Resource name suffix | Auto-generated | Any string |
| `searchServiceSku` | AI Search SKU | `basic` | `basic`, `standard`, `standard2`, `standard3` |
| `functionAppSku` | Function App plan SKU | `Y1` | `Y1` (Consumption) |
| `tags` | Resource tags | See parameters.json | Any object |

## Resource Naming Convention

Resources follow Azure naming best practices:

- **Storage Account**: `stfoundry{env}{uniqueSuffix}` (no hyphens, lowercase)
- **Function App**: `func-foundry-{env}-{uniqueSuffix}`
- **Static Web App**: `swa-foundry-{env}-{uniqueSuffix}`
- **Key Vault**: `kv-foundry-{uniqueSuffix}` (max 24 chars)
- **App Insights**: `appi-foundry-{env}-{uniqueSuffix}`
- **AI Search**: `srch-foundry-{env}-{uniqueSuffix}`
- **Log Analytics**: `log-foundry-{env}-{uniqueSuffix}`

## Support and Contribution

For issues or questions:
1. Check the troubleshooting section above
2. Review Azure documentation for specific services
3. Open an issue in the repository

## Related Issues

- Issue #3: Static Web App deployment and configuration
- Issue #7: Function App implementation and deployment

These issues depend on the outputs and configuration provided by this infrastructure deployment.
