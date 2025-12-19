# Deployment Summary - Foundry Observability Demo Infrastructure

## Overview

This document provides a comprehensive summary of the infrastructure deployment for the Foundry Observability Demo project.

## Deployment Details

### Target Environment
- **Resource Group**: `rg-foundry-demo` (Switzerland North)
- **Resources Location**: Sweden Central
- **Environment**: Demo/Development

### Deployed Resources

| # | Resource Type | Resource Name Pattern | Purpose |
|---|--------------|----------------------|---------|
| 1 | Storage Account | `stfoundry{env}{suffix}` | Function app storage and data persistence |
| 2 | Blob Service | (child of Storage) | Blob storage service |
| 3 | Blob Container | `function-releases` | Function app deployments |
| 4 | Log Analytics Workspace | `log-foundry-{env}-{suffix}` | Centralized logging |
| 5 | Application Insights | `appi-foundry-{env}-{suffix}` | Application monitoring and telemetry |
| 6 | Azure AI Search | `srch-foundry-{env}-{suffix}` | Search and vector store (Basic SKU) |
| 7 | Key Vault | `kv-foundry-{suffix}` | Secrets management |
| 8 | App Service Plan | `asp-func-foundry-{env}-{suffix}` | Consumption plan for Function App |
| 9 | Function App | `func-foundry-{env}-{suffix}` | Python 3.11 backend API (Linux) |
| 10 | Static Web App | `swa-foundry-{env}-{suffix}` | Frontend hosting (Free tier) |
| 11 | Static Web App Config | (child of Static Web App) | App settings for Static Web App |
| 12 | Role Assignment | (Function App → Key Vault) | Key Vault Secrets User role |
| 13 | Role Assignment | (Function App → Storage) | Storage Blob Data Contributor role |

**Total**: 13 Azure resources

### Security Configuration

#### Managed Identity
- Function App uses **System-Assigned Managed Identity**
- Principal ID available in deployment outputs for further role assignments

#### RBAC Roles
- **Key Vault Secrets User** on Key Vault → Function App can read secrets
- **Storage Blob Data Contributor** on Storage Account → Function App can read/write blobs

#### Network Security
- All resources enforce HTTPS only
- Minimum TLS version: 1.2
- Key Vault soft-delete enabled (90 days retention)
- Storage Account: Public blob access disabled
- Default network action: Allow (with Azure Services bypass)

### Configuration Outputs

The deployment provides comprehensive outputs for downstream use:

#### For Function App (Issue #7)
```json
{
  "AzureWebJobsStorage": "<connection-string>",
  "WEBSITE_CONTENTAZUREFILECONNECTIONSTRING": "<connection-string>",
  "WEBSITE_CONTENTSHARE": "<function-app-name>",
  "FUNCTIONS_EXTENSION_VERSION": "~4",
  "FUNCTIONS_WORKER_RUNTIME": "python",
  "APPLICATIONINSIGHTS_CONNECTION_STRING": "<appinsights-connection>",
  "APPINSIGHTS_INSTRUMENTATIONKEY": "<instrumentation-key>",
  "AZURE_SEARCH_ENDPOINT": "https://<search-name>.search.windows.net",
  "AZURE_KEY_VAULT_ENDPOINT": "<keyvault-uri>",
  "STORAGE_ACCOUNT_NAME": "<storage-name>"
}
```

#### For Static Web App (Issue #3)
```json
{
  "APPLICATIONINSIGHTS_CONNECTION_STRING": "<appinsights-connection>",
  "AZURE_FUNCTION_APP_URL": "https://<function-app-hostname>"
}
```

## Deployment Methods

### Method 1: Automated Script
```bash
cd infra
./deploy.sh demo
```

### Method 2: Manual Azure CLI
```bash
cd infra
az deployment group create \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json
```

### Method 3: Azure Portal
1. Navigate to Resource Groups → rg-foundry-demo
2. Click "Deploy a custom template"
3. Click "Build your own template in the editor"
4. Copy contents of `main.bicep`
5. Click "Save" and configure parameters
6. Review and create

## Post-Deployment Steps

### Automated (via deploy.sh)
✅ Store Azure AI Search admin key in Key Vault  
✅ Store Storage Account key in Key Vault

### Manual Steps Required

#### 1. Microsoft Foundry Project Creation
⚠️ **Required Manual Action**

Foundry projects cannot be created via IaC (preview limitations).

**Steps**:
1. Go to Azure Portal → Microsoft Foundry / Azure AI Studio
2. Create new project:
   - Name: `foundry-observability-demo`
   - Resource Group: `rg-foundry-demo`
   - Location: `Sweden Central`
3. Link deployed resources:
   - Application Insights: `appi-foundry-demo-*`
   - Storage Account: `stfoundrydemo*`
   - Azure AI Search: `srch-foundry-demo-*`

#### 2. Static Web App Deployment Token
For GitHub Actions deployment:
```bash
az staticwebapp secrets list \
  --name <static-web-app-name> \
  --resource-group rg-foundry-demo \
  --query properties.apiKey -o tsv
```
Store in GitHub Secrets as: `AZURE_STATIC_WEB_APPS_API_TOKEN`

## Validation

### Resource Count
```bash
az resource list \
  --resource-group rg-foundry-demo \
  --query "length(@)"
```
Expected: 13 resources

### Function App Status
```bash
az functionapp show \
  --name <function-app-name> \
  --resource-group rg-foundry-demo \
  --query state
```
Expected: "Running"

### Connectivity Tests
```bash
# Function App
curl -I https://<function-app-hostname>

# Static Web App
curl -I https://<static-web-app-hostname>
```

## Files Delivered

### Infrastructure Code
- ✅ `infra/main.bicep` - Main Bicep template (13,905 bytes)
- ✅ `infra/parameters.json` - Parameter file (524 bytes)
- ✅ `infra/.bicepconfig.json` - Bicep linter configuration
- ✅ `infra/deploy.sh` - Automated deployment script
- ✅ `infra/README.md` - Comprehensive deployment guide (12,787 bytes)

### Documentation
- ✅ `README.md` - Updated project README
- ✅ `.env.template` - Environment variables template
- ✅ `scripts/generate-env.sh` - Auto-generate .env from deployment

### Configuration
- ✅ `.gitignore` - Updated with Azure/Bicep patterns

## Security Compliance

### Secrets Management
- ✅ No secrets committed to repository
- ✅ All secrets stored in Azure Key Vault
- ✅ Connection strings use Key Vault references
- ✅ Managed identities preferred over access keys

### Access Control
- ✅ RBAC roles with least privilege
- ✅ System-assigned managed identities
- ✅ Key Vault RBAC authorization enabled
- ✅ Service-to-service authentication via managed identity

### Network Security
- ✅ HTTPS enforced on all endpoints
- ✅ TLS 1.2 minimum version
- ✅ FTPS disabled on Function App
- ✅ Public blob access disabled

## Cost Considerations

### Estimated Monthly Cost (Sweden Central)

| Resource | SKU/Tier | Estimated Cost |
|----------|----------|----------------|
| Storage Account | Standard LRS | ~$0.50 |
| Function App | Consumption (Y1) | First 1M executions free |
| App Insights | Standard | Based on ingestion |
| Log Analytics | Pay-as-you-go | Based on ingestion |
| Azure AI Search | Basic | ~$75/month |
| Key Vault | Standard | $0.03 per 10K operations |
| Static Web App | Free | $0 |

**Total Estimated**: ~$80-100/month (excluding data ingestion)

## Troubleshooting

### Common Issues

1. **Role Assignment Fails**
   - Cause: Insufficient permissions
   - Solution: Ensure Owner or Contributor + User Access Administrator roles

2. **Key Vault Access Denied**
   - Cause: RBAC not propagated
   - Solution: Wait 5-10 minutes for Azure AD replication

3. **Function App Not Starting**
   - Cause: Storage connection issue
   - Solution: Verify storage account exists and Function App has access

## Next Steps

### For Issue #7 (Function App)
1. Use `functionAppSettings` output for configuration
2. Deploy Python function code
3. Configure CI/CD pipeline
4. Test API endpoints

### For Issue #3 (Static Web App)
1. Use `staticWebAppSettings` output for configuration
2. Deploy frontend code
3. Configure GitHub Actions deployment
4. Test web application

### For Foundry Integration
1. Complete manual Foundry project creation
2. Note Foundry endpoint and project ID
3. Store in Key Vault:
   ```bash
   az keyvault secret set \
     --vault-name <kv-name> \
     --name FoundryProjectEndpoint \
     --value <endpoint>
   ```

## Support

- **Documentation**: See `infra/README.md` for detailed guides
- **Issues**: Open GitHub issue with `infra` label
- **Azure Support**: Use Azure Portal support for service-specific issues

## Version History

- **v1.0** (Initial): Complete infrastructure deployment with all required resources
  - 13 Azure resources
  - Sweden Central deployment
  - Comprehensive documentation
  - Automated deployment scripts
  - Security best practices implemented

---

**Deployment Status**: ✅ Ready for Production  
**Last Updated**: 2025-12-19  
**Issue**: #B - Bicep/IaC: Deploy minimal demo infra (Sweden Central)
