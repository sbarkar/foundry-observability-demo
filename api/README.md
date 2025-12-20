# Azure Functions API - Foundry Observability Demo

A stateless Python Azure Functions API for chat completion using Azure OpenAI (via Foundry) with OpenTelemetry instrumentation and optional RAG capabilities.

## Features

- **Health Check Endpoint** (`/api/health`): No authentication required
- **Chat Endpoint** (`/api/chat`): Entra ID JWT authentication
- **Azure OpenAI Integration**: Uses DefaultAzureCredential for managed identity
- **Optional RAG**: Query Azure AI Search and inject context into prompts
- **OpenTelemetry**: Full instrumentation with Application Insights
- **Correlation IDs**: Every response includes a unique correlation ID for tracking
- **Stateless**: No database, metadata-only logging (no user content stored)
- **Security**: JWT validation with configurable issuer/audience

## Prerequisites

- Python 3.9 or higher
- Azure Functions Core Tools 4.x
- Azure subscription with:
  - Azure OpenAI resource (or Foundry deployment)
  - Application Insights instance
  - (Optional) Azure AI Search service for RAG
  - Entra ID app registration for JWT authentication

## Local Development Setup

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Configure Local Settings

Copy the example settings file:

```bash
cp local.settings.example.json local.settings.json
```

Edit `local.settings.json` with your configuration:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=your-key;IngestionEndpoint=https://[region].in.applicationinsights.azure.com/",
    
    "AZURE_OPENAI_ENDPOINT": "https://[your-resource].openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
    
    "ENTRA_ISSUER": "https://login.microsoftonline.com/[tenant-id]/v2.0",
    "ENTRA_AUDIENCE": "api://[your-app-id]",
    "JWT_VALIDATION_ENABLED": "true",
    
    "AZURE_SEARCH_ENDPOINT": "https://[your-search].search.windows.net",
    "AZURE_SEARCH_INDEX_NAME": "your-index",
    "AZURE_SEARCH_TOP_K": "3",
    "RAG_ENABLED": "false"
  }
}
```

### 3. Azure Authentication

For local development with DefaultAzureCredential, authenticate using Azure CLI:

```bash
az login
```

Or set environment variables for service principal:

```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
```

### 4. Run the Function App

```bash
func start
```

The API will be available at:
- `http://localhost:7071/api/health`
- `http://localhost:7071/api/chat`

## Testing

### Run Unit Tests

```bash
cd api
python -m pytest tests/
```

Or run individual test files:

```bash
python -m pytest tests/test_health.py
python -m pytest tests/test_auth.py
python -m pytest tests/test_chat.py
python -m pytest tests/test_correlation.py
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=. --cov-report=html
```

### Manual Testing

#### Health Check

```bash
curl http://localhost:7071/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "foundry-observability-demo-api",
  "correlationId": "uuid-here"
}
```

#### Chat Endpoint (JWT Disabled)

For local testing, you can disable JWT validation:

```json
// In local.settings.json
"JWT_VALIDATION_ENABLED": "false"
```

Then test:

```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

#### Chat Endpoint (JWT Enabled)

With JWT validation enabled:

```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message": "Hello, how are you?"}'
```

#### Chat with RAG

Enable RAG in configuration, then:

```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message": "What is in the documentation?", "enableRag": true}'
```

## Configuration Reference

### Required Settings

| Setting | Description |
|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Deployment/model name (e.g., "gpt-4") |
| `ENTRA_ISSUER` | Entra ID issuer URL (e.g., `https://login.microsoftonline.com/{tenant-id}/v2.0`) |
| `ENTRA_AUDIENCE` | Expected audience in JWT (e.g., `api://{app-id}`) |

### Optional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `JWT_VALIDATION_ENABLED` | Enable/disable JWT validation | `true` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection string | None (telemetry disabled) |
| `AZURE_OPENAI_API_VERSION` | API version for OpenAI | `2024-02-15-preview` |
| `RAG_ENABLED` | Enable RAG globally | `false` |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint | None |
| `AZURE_SEARCH_INDEX_NAME` | Search index name | None |
| `AZURE_SEARCH_TOP_K` | Number of documents to retrieve | `3` |

## API Reference

### GET /api/health

Health check endpoint.

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "service": "foundry-observability-demo-api",
  "correlationId": "uuid"
}
```

### POST /api/chat

Chat completion endpoint with optional RAG.

**Authentication:** Bearer token (Entra ID JWT)

**Request:**
```json
{
  "message": "Your question here",
  "enableRag": false
}
```

**Response (Success):**
```json
{
  "answer": "AI response here",
  "correlationId": "uuid",
  "model": "gpt-4",
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

**Response (Error):**
```json
{
  "error": "Error Type",
  "message": "Error description",
  "correlationId": "uuid"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad request (invalid JSON, missing fields, message too long)
- `401`: Unauthorized (missing or invalid JWT token)
- `500`: Server error (configuration issues, OpenAI failures)

## Architecture

### Stateless Design

- No persistent storage or database
- Each request is independent
- No session state maintained

### Logging Policy

- **Metadata only**: Logs include request metadata, token counts, model names
- **No user content**: User messages and AI responses are never logged
- **Correlation IDs**: Every request has a unique ID for tracking

### OpenTelemetry

The API instruments:
- HTTP requests (automatic)
- Custom spans for OpenAI calls
- Custom spans for RAG searches
- Attributes for correlation IDs, model info, token usage (no content)

### Security

- JWT validation against Entra ID
- Configurable issuer and audience
- DefaultAzureCredential for Azure SDK calls (supports Managed Identity)
- No secrets in code or logs

## Deployment

### Deploy to Azure

1. Create Azure Function App:
   ```bash
   az functionapp create \
     --resource-group your-rg \
     --name your-function-app \
     --consumption-plan-location eastus \
     --runtime python \
     --runtime-version 3.9 \
     --storage-account yourstorage \
     --os-type Linux
   ```

2. Configure app settings (same as local.settings.json Values):
   ```bash
   az functionapp config appsettings set \
     --name your-function-app \
     --resource-group your-rg \
     --settings \
       AZURE_OPENAI_ENDPOINT="https://..." \
       AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
       ENTRA_ISSUER="https://..." \
       ENTRA_AUDIENCE="api://..."
   ```

3. Enable Managed Identity:
   ```bash
   az functionapp identity assign \
     --name your-function-app \
     --resource-group your-rg
   ```

4. Grant permissions to Azure OpenAI and Azure Search:
   ```bash
   # Get the managed identity principal ID
   PRINCIPAL_ID=$(az functionapp identity show \
     --name your-function-app \
     --resource-group your-rg \
     --query principalId -o tsv)
   
   # Grant Cognitive Services OpenAI User role
   az role assignment create \
     --assignee $PRINCIPAL_ID \
     --role "Cognitive Services OpenAI User" \
     --scope /subscriptions/{subscription-id}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{openai-account}
   ```

5. Deploy:
   ```bash
   func azure functionapp publish your-function-app
   ```

## Troubleshooting

### Authentication Issues

- Verify `ENTRA_ISSUER` and `ENTRA_AUDIENCE` match your Entra ID app registration
- Check JWT token is not expired
- Ensure `Authorization: Bearer {token}` header format is correct

### OpenAI Connection Issues

- Verify `AZURE_OPENAI_ENDPOINT` is correct
- Check DefaultAzureCredential has permissions
- Verify deployment name exists in your OpenAI resource

### RAG Not Working

- Ensure `RAG_ENABLED=true` in configuration
- Verify Azure Search endpoint and index name
- Check managed identity has "Search Index Data Reader" role

### Local Development

- Run `az login` before starting the function
- Ensure Azure Functions Core Tools is installed: `func --version`
- Check Python version: `python --version` (should be 3.9+)

## VS Code DevContainer

A devcontainer configuration is provided in `.devcontainer/devcontainer.json` for consistent development environments.

## License

See LICENSE file in repository root.
