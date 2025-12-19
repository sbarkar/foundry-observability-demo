# Azure Foundry Observability Demo

A comprehensive Azure demo showcasing a production-ready GenAI chat application with:
- **Static Web App** frontend with simple chat UI
- **Azure Functions** Python backend
- **Entra ID (Azure AD)** authentication using MSAL
- **Azure AI Foundry** (Azure OpenAI) for chat completions
- **Azure AI Search** for Retrieval Augmented Generation (RAG)
- **OpenTelemetry** and **Application Insights** for full observability
- **Infrastructure as Code** with Bicep

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌────────────────────┐
│  Static Web App │────────▶│  Azure Functions │────────▶│  Azure OpenAI      │
│  (React/HTML)   │  HTTPS  │  (Python + Auth) │  RBAC   │  (GPT-4)           │
└─────────────────┘         └──────────────────┘         └────────────────────┘
         │                           │                              
         │                           │                    ┌────────────────────┐
         │                           └───────────────────▶│  Azure AI Search   │
         │                                         RBAC   │  (RAG)             │
         │                                                └────────────────────┘
         │                           ┌──────────────────┐
         └──────────────────────────▶│  Entra ID        │
                  OAuth 2.0          │  (MSAL Auth)     │
                                     └──────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │  App Insights    │
                                     │  (Telemetry)     │
                                     └──────────────────┘
```

## 📋 Features

### Authentication & Authorization
- **Entra ID (Azure AD)** integration using MSAL
- OAuth 2.0 token-based authentication
- Frontend: MSAL.js for browser-based authentication
- Backend: Token validation and user identity

### AI & Search
- **Azure OpenAI** chat completions with GPT-4
- **Azure AI Search** for RAG (Retrieval Augmented Generation)
- Context-aware responses using retrieved documents
- Content safety filtering

### Observability & Telemetry
- **OpenTelemetry** instrumentation
- **Application Insights** integration
- **Tracked Metrics:**
  - ✅ Correlation IDs for request tracing
  - ✅ Token usage (prompt, completion, total)
  - ✅ Request latency in milliseconds
  - ✅ Content safety flags
  - ✅ RAG document retrieval counts
  - ✅ Error rates and exceptions

### Infrastructure as Code
- **Bicep** templates for all Azure resources
- Resource group: `rg-foundry-demo`
- Managed identities for secure, secretless access
- RBAC assignments for service-to-service auth

## 🚀 Prerequisites

- **Azure Subscription** with appropriate permissions
- **Azure CLI** (v2.50+) installed
- **Python 3.11** or later
- **Azure Functions Core Tools** (v4.x)
- **Node.js** (v18+) for Static Web App development
- **Azure AD App Registration** for authentication

## 📦 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/sbarkar/foundry-observability-demo.git
cd foundry-observability-demo
```

### 2. Set Up Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Click "New registration"
   - Name: `foundry-demo-app`
   - Supported account types: Single tenant
   - Redirect URI: `Web` - `http://localhost:8080` (for local dev)
3. Note the **Application (client) ID** and **Directory (tenant) ID**
4. Under "Authentication":
   - Add platform: Single-page application
   - Redirect URI: Your Static Web App URL (after deployment)
   - Enable "Access tokens" and "ID tokens"
5. Under "API permissions":
   - Add Microsoft Graph → Delegated → `User.Read`
6. Under "Expose an API":
   - Add a scope: `access_as_user`
   - Note the Application ID URI

### 3. Deploy Infrastructure

Update `infrastructure/parameters.json` with your values:

```json
{
  "tenantId": "YOUR_TENANT_ID",
  "clientId": "YOUR_CLIENT_ID",
  "openAIServiceName": "aoai-foundry-demo-UNIQUE",
  "searchServiceName": "srch-foundry-demo-UNIQUE",
  "staticWebAppName": "swa-foundry-demo-UNIQUE",
  "functionAppName": "func-foundry-demo-UNIQUE",
  "appInsightsName": "appi-foundry-demo-UNIQUE"
}
```

Deploy with Azure CLI:

```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Deploy infrastructure
az deployment sub create \
  --location eastus \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/parameters.json

# Get deployment outputs
az deployment sub show \
  --name resources-deployment \
  --query properties.outputs
```

**Note the outputs:** Function App URL, Static Web App URL, App Insights Connection String

### 4. Configure Azure OpenAI

Deploy a GPT-4 model in your Azure OpenAI service:

```bash
# Get OpenAI resource name from deployment
OPENAI_NAME="aoai-foundry-demo-UNIQUE"

# Deploy GPT-4 model
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group rg-foundry-demo \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

### 5. Set Up Azure AI Search Index (Optional for RAG)

Create a search index and upload sample documents:

```bash
# Example: Create index with Azure CLI or Portal
# Add your documents to enable RAG functionality
```

### 6. Configure Backend for Local Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure local settings
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your Azure resource values

# Start the Function App locally
func start
```

Your backend will be available at `http://localhost:7071`

### 7. Configure Frontend for Local Development

Update `frontend/config.js` with your values:

```javascript
const config = {
    auth: {
        clientId: 'YOUR_CLIENT_ID',
        authority: 'https://login.microsoftonline.com/YOUR_TENANT_ID',
        redirectUri: 'http://localhost:8080'
    },
    apiEndpoint: 'http://localhost:7071',
    apiScopes: ['api://YOUR_CLIENT_ID/access_as_user']
};
```

Serve the frontend locally:

```bash
cd frontend

# Using Python's built-in HTTP server
python -m http.server 8080

# Or using Node.js http-server
npx http-server -p 8080
```

Open browser to `http://localhost:8080`

### 8. Test the Application

1. Click "Sign In" to authenticate with Entra ID
2. Type a message in the chat input
3. Toggle "Enable RAG" to use document retrieval
4. View telemetry data in the status bar:
   - Correlation ID
   - Latency
   - Token usage

## 📊 Viewing Observability Data

### Application Insights

1. Go to Azure Portal → Your App Insights resource
2. View dashboards:
   - **Live Metrics**: Real-time telemetry
   - **Transaction Search**: Find requests by correlation ID
   - **Application Map**: Service dependencies
   - **Performance**: Latency analysis
   - **Failures**: Error tracking

### Custom Queries (Kusto/KQL)

Query for chat requests with token usage:

```kql
traces
| where message contains "chat_request"
| extend correlationId = tostring(customDimensions.correlation_id)
| extend totalTokens = toint(customDimensions.total_tokens)
| extend latencySeconds = todouble(customDimensions.latency_seconds)
| project timestamp, correlationId, totalTokens, latencySeconds
| order by timestamp desc
```

Query for average latency by hour:

```kql
traces
| where message contains "chat_request"
| extend latencySeconds = todouble(customDimensions.latency_seconds)
| summarize avgLatency=avg(latencySeconds), requestCount=count() by bin(timestamp, 1h)
| order by timestamp desc
```

## 🔧 Configuration Reference

### Environment Variables (Backend)

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | Entra ID tenant ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_ID` | App registration client ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://aoai-demo.openai.azure.com/` |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint | `https://srch-demo.search.windows.net` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection string | `InstrumentationKey=...` |

### Frontend Configuration

Update `frontend/config.js` with:
- `clientId`: Your Azure AD app registration client ID
- `authority`: Your tenant-specific authority URL
- `apiEndpoint`: Your Function App URL
- `apiScopes`: API permissions scope

## 🚢 Deployment to Azure

### Deploy Backend (Function App)

```bash
cd backend

# Package and deploy
func azure functionapp publish func-foundry-demo-UNIQUE --python
```

### Deploy Frontend (Static Web App)

```bash
# Using Azure CLI
az staticwebapp create \
  --name swa-foundry-demo-UNIQUE \
  --resource-group rg-foundry-demo \
  --source frontend \
  --location eastus \
  --branch main
```

Or use GitHub Actions for CI/CD (see `.github/workflows` for examples)

## 🔒 Security Best Practices

✅ **Implemented:**
- No secrets in source code (all use environment variables)
- Managed Identity for Azure service authentication
- RBAC for least-privilege access
- HTTPS-only communication
- Token-based authentication (OAuth 2.0)
- Content safety filtering via Azure OpenAI

⚠️ **Production Considerations:**
- Enable Azure AD token validation in backend
- Implement rate limiting
- Add input sanitization
- Enable Azure DDoS Protection
- Configure Azure Front Door or CDN
- Set up monitoring alerts
- Implement comprehensive logging

## 📁 Project Structure

```
foundry-observability-demo/
├── infrastructure/          # Bicep IaC templates
│   ├── main.bicep          # Main deployment template
│   ├── resources.bicep     # Resource definitions
│   └── parameters.json     # Configuration parameters
├── backend/                # Azure Functions backend
│   ├── api/
│   │   └── function_app.py # Main function with chat endpoint
│   ├── requirements.txt    # Python dependencies
│   ├── host.json          # Function app configuration
│   └── local.settings.json.example
├── frontend/               # Static Web App frontend
│   ├── index.html         # Main HTML page
│   ├── style.css          # Styles
│   ├── app.js             # Chat logic
│   └── config.js          # Configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🐛 Troubleshooting

### Issue: CORS errors when calling backend
**Solution:** Ensure your Static Web App URL is added to Function App CORS settings

### Issue: Authentication fails
**Solution:** 
- Verify tenant ID and client ID in config
- Check redirect URI matches exactly
- Ensure user has required permissions

### Issue: OpenAI returns 401 Unauthorized
**Solution:**
- Verify Function App managed identity has "Cognitive Services OpenAI User" role
- Check AZURE_OPENAI_ENDPOINT is correct

### Issue: Search returns empty results
**Solution:**
- Create a search index with documents
- Verify Function App has "Search Index Data Reader" role
- Check AZURE_SEARCH_ENDPOINT is correct

## 📚 Additional Resources

- [Azure Functions Python Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [MSAL.js Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Application Insights Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue in the GitHub repository.
