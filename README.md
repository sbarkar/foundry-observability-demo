# foundry-observability-demo

A repo showcasing an example of how to use Microsoft Foundry to deploy a simple and compliant GenAI use case using Microsoft native tools.

## Components

### Backend API (`/api`)

Python-based Azure Functions API providing stateless chat completion with comprehensive observability:

- **Health Check Endpoint** (`/api/health`): No authentication required
- **Chat Endpoint** (`/api/chat`): Entra ID JWT authentication
- **Azure OpenAI Integration**: Uses DefaultAzureCredential for managed identity
- **Optional RAG**: Query Azure AI Search and inject context into prompts
- **OpenTelemetry**: Full instrumentation with Application Insights
- **Stateless Design**: No database, metadata-only logging (no user content stored)

See [api/README.md](api/README.md) for detailed documentation, local development setup, and deployment instructions.

## Features

- ✅ Entra ID JWT authentication with configurable issuer/audience
- ✅ Azure OpenAI integration via Foundry deployment
- ✅ Optional RAG with Azure AI Search
- ✅ Correlation IDs for request tracking
- ✅ OpenTelemetry instrumentation to Application Insights
- ✅ Stateless, metadata-only logging (no user content stored)
- ✅ Comprehensive unit tests (16 tests)
- ✅ VS Code devcontainer support

## Quick Start

```bash
# Navigate to API directory
cd api

# Install dependencies
pip install -r requirements.txt

# Configure settings (copy and edit)
cp local.settings.example.json local.settings.json

# Authenticate with Azure
az login

# Run locally
func start
```

## Security

- No secrets in code or logs
- User content never logged (metadata only)
- JWT validation with Entra ID
- DefaultAzureCredential for Azure SDK calls
- Safe error messages exposed to clients

## License

See [LICENSE](LICENSE) file.
