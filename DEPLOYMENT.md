# Deployment Guide

This guide walks through deploying the Azure Foundry Observability Demo step-by-step.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Azure subscription with Owner or Contributor access
- [ ] Azure CLI installed and logged in (`az login`)
- [ ] Python 3.11+ installed
- [ ] Azure Functions Core Tools v4.x installed
- [ ] Git installed

## Step 1: Azure AD App Registration

### 1.1 Create App Registration

```bash
# Set variables
APP_NAME="foundry-demo-app"

# Create app registration
APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --web-redirect-uris "http://localhost:8080" \
  --enable-access-token-issuance true \
  --enable-id-token-issuance true \
  --query appId -o tsv)

echo "Application (Client) ID: $APP_ID"

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant ID: $TENANT_ID"

# Add Microsoft Graph User.Read permission
GRAPH_USER_READ_ID="e1fe6dd8-ba31-4d61-89e7-88639da4683d"
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions $GRAPH_USER_READ_ID=Scope

# Grant admin consent (requires admin privileges)
az ad app permission admin-consent --id $APP_ID
```

### 1.2 Expose an API

```bash
# Set Application ID URI
az ad app update --id $APP_ID \
  --identifier-uris "api://$APP_ID"

# Add a scope
SCOPE_ID=$(uuidgen)
az ad app update --id $APP_ID \
  --app-roles '[{
    "allowedMemberTypes": ["User"],
    "description": "Access the API as a user",
    "displayName": "Access as user",
    "id": "'$SCOPE_ID'",
    "isEnabled": true,
    "value": "access_as_user"
  }]'
```

### 1.3 Save Configuration

Save these values for later:
- Application (Client) ID: `$APP_ID`
- Tenant ID: `$TENANT_ID`

## Step 2: Deploy Azure Infrastructure

### 2.1 Update Parameters

Edit `infrastructure/parameters.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2018-05-01/subscriptionDeploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "resourceGroupName": {
      "value": "rg-foundry-demo"
    },
    "location": {
      "value": "eastus"
    },
    "openAIServiceName": {
      "value": "aoai-foundry-demo-SUFFIX"
    },
    "searchServiceName": {
      "value": "srch-foundry-demo-SUFFIX"
    },
    "staticWebAppName": {
      "value": "swa-foundry-demo-SUFFIX"
    },
    "functionAppName": {
      "value": "func-foundry-demo-SUFFIX"
    },
    "appInsightsName": {
      "value": "appi-foundry-demo-SUFFIX"
    },
    "tenantId": {
      "value": "YOUR_TENANT_ID"
    },
    "clientId": {
      "value": "YOUR_CLIENT_ID"
    }
  }
}
```

Replace:
- `SUFFIX` with a unique identifier (e.g., your initials + date)
- `YOUR_TENANT_ID` with `$TENANT_ID`
- `YOUR_CLIENT_ID` with `$APP_ID`

### 2.2 Deploy Infrastructure

```bash
# Set subscription
SUBSCRIPTION_ID="YOUR_SUBSCRIPTION_ID"
az account set --subscription $SUBSCRIPTION_ID

# Validate template
az deployment sub validate \
  --location eastus \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/parameters.json

# Deploy (takes 5-10 minutes)
az deployment sub create \
  --name foundry-demo-deployment \
  --location eastus \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/parameters.json

# Get outputs
az deployment sub show \
  --name foundry-demo-deployment \
  --query properties.outputs
```

Save the outputs:
- `staticWebAppUrl`
- `functionAppUrl`
- `appInsightsConnectionString`
- `openAIEndpoint`
- `searchEndpoint`

## Step 3: Configure Azure OpenAI

### 3.1 Deploy GPT-4 Model

```bash
# Get OpenAI service name from parameters
OPENAI_NAME="aoai-foundry-demo-SUFFIX"
RESOURCE_GROUP="rg-foundry-demo"

# List available models
az cognitiveservices account deployment list \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP

# Deploy GPT-4 (or GPT-3.5-turbo for lower cost)
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

## Step 4: Setup Azure AI Search (Optional for RAG)

### 4.1 Create Search Index

For RAG functionality, create a search index with sample documents:

```bash
SEARCH_NAME="srch-foundry-demo-SUFFIX"

# Create index (example schema)
az search index create \
  --service-name $SEARCH_NAME \
  --resource-group $RESOURCE_GROUP \
  --name documents \
  --fields '[
    {"name":"id","type":"Edm.String","key":true,"searchable":false},
    {"name":"title","type":"Edm.String","searchable":true},
    {"name":"content","type":"Edm.String","searchable":true,"analyzer":"en.microsoft"}
  ]'
```

### 4.2 Upload Sample Documents

Create a `sample-docs.json` file:

```json
[
  {
    "id": "1",
    "title": "Azure Services Overview",
    "content": "Azure provides cloud services including compute, storage, networking, and AI capabilities..."
  },
  {
    "id": "2",
    "title": "OpenAI Integration",
    "content": "Azure OpenAI Service provides REST API access to powerful language models..."
  }
]
```

Upload documents:

```bash
az search index upload \
  --service-name $SEARCH_NAME \
  --resource-group $RESOURCE_GROUP \
  --index-name documents \
  --documents @sample-docs.json
```

## Step 5: Configure and Deploy Backend

### 5.1 Update App Registration for Backend

```bash
FUNCTION_URL="https://func-foundry-demo-SUFFIX.azurewebsites.net"

# Add Function App URL to redirect URIs
az ad app update --id $APP_ID \
  --web-redirect-uris "http://localhost:8080" "$FUNCTION_URL"
```

### 5.2 Deploy Function App

```bash
cd backend

# Install dependencies locally (optional, for testing)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Deploy to Azure
func azure functionapp publish func-foundry-demo-SUFFIX --python

# Verify deployment
curl https://func-foundry-demo-SUFFIX.azurewebsites.net/api/health
```

## Step 6: Configure and Deploy Frontend

### 6.1 Update Frontend Configuration

Edit `frontend/config.js`:

```javascript
const config = {
    auth: {
        clientId: 'YOUR_CLIENT_ID',  // From Step 1
        authority: 'https://login.microsoftonline.com/YOUR_TENANT_ID',
        redirectUri: 'https://YOUR_STATIC_WEB_APP_URL'  // From Step 2
    },
    apiEndpoint: 'https://func-foundry-demo-SUFFIX.azurewebsites.net',
    apiScopes: ['api://YOUR_CLIENT_ID/access_as_user']
};
```

### 6.2 Deploy to Static Web App

```bash
cd frontend

# Deploy using Azure CLI
SWA_NAME="swa-foundry-demo-SUFFIX"

az staticwebapp update \
  --name $SWA_NAME \
  --resource-group $RESOURCE_GROUP

# Or manually upload via Portal:
# 1. Go to Static Web App in Azure Portal
# 2. Go to "Configuration" → "Application settings"
# 3. Upload frontend files
```

## Step 7: Update CORS Settings

```bash
FUNCTION_NAME="func-foundry-demo-SUFFIX"
SWA_URL="https://YOUR_STATIC_WEB_APP_URL"

# Add Static Web App URL to Function App CORS
az functionapp cors add \
  --name $FUNCTION_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "$SWA_URL"

# Enable credentials
az functionapp cors credentials \
  --name $FUNCTION_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable true
```

## Step 8: Test the Deployment

### 8.1 Access the Application

1. Navigate to your Static Web App URL
2. Click "Sign In"
3. Authenticate with your Azure AD account
4. Send a test message
5. Verify response and telemetry

### 8.2 Verify Telemetry in Application Insights

```bash
# Get App Insights URL
echo "https://portal.azure.com/#@$TENANT_ID/resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Insights/components/appi-foundry-demo-SUFFIX"
```

Navigate to:
- **Live Metrics**: See real-time requests
- **Transaction Search**: Find your test request by correlation ID
- **Logs**: Run KQL queries

### 8.3 Test Query

```kql
traces
| where timestamp > ago(1h)
| where message contains "chat_request"
| project timestamp, message, customDimensions
| order by timestamp desc
```

## Step 9: Local Development Setup

### 9.1 Backend Local Setup

```bash
cd backend

# Create local.settings.json
cp local.settings.json.example local.settings.json

# Edit local.settings.json with your values
nano local.settings.json
```

Add:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_TENANT_ID": "YOUR_TENANT_ID",
    "AZURE_CLIENT_ID": "YOUR_CLIENT_ID",
    "AZURE_OPENAI_ENDPOINT": "https://aoai-foundry-demo-SUFFIX.openai.azure.com/",
    "AZURE_SEARCH_ENDPOINT": "https://srch-foundry-demo-SUFFIX.search.windows.net",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "YOUR_CONNECTION_STRING"
  }
}
```

Start locally:
```bash
func start
```

### 9.2 Frontend Local Setup

```bash
cd frontend

# Update config.js for local development
# Set redirectUri to http://localhost:8080
# Set apiEndpoint to http://localhost:7071

# Serve locally
python -m http.server 8080
```

Update Azure AD redirect URIs:
```bash
az ad app update --id $APP_ID \
  --web-redirect-uris "http://localhost:8080" "$FUNCTION_URL" "$SWA_URL"
```

## Troubleshooting

### Deployment Fails

- **Check quotas**: Ensure your subscription has capacity for services
- **Check naming**: Azure service names must be globally unique
- **Check permissions**: You need Contributor or Owner role

### Authentication Fails

- **Redirect URI**: Must match exactly (http vs https, trailing slash)
- **Tenant**: Ensure using correct tenant ID
- **Permissions**: Grant admin consent for Microsoft Graph

### OpenAI Returns 401

- **Role assignment**: Function App needs "Cognitive Services OpenAI User" role
- **Deployment**: Ensure GPT-4 model is deployed
- **Endpoint**: Verify AZURE_OPENAI_ENDPOINT format

### No Telemetry in App Insights

- **Connection string**: Verify APPLICATIONINSIGHTS_CONNECTION_STRING is set
- **Wait time**: Telemetry can take 1-2 minutes to appear
- **Sampling**: Check sampling settings in host.json

## Clean Up Resources

To delete all resources:

```bash
az group delete --name rg-foundry-demo --yes --no-wait

# Also delete app registration
az ad app delete --id $APP_ID
```

## Next Steps

- Configure monitoring alerts
- Add more sophisticated RAG logic
- Implement conversation history storage
- Add user feedback collection
- Set up CI/CD pipelines
- Configure production security hardening
