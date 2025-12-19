# Foundry Observability Demo

A repository showcasing an example of how to use Microsoft Foundry to deploy a simple and compliant GenAI use case using Microsoft native tools.

## Overview

This project demonstrates observability and monitoring best practices for GenAI applications built with Microsoft Foundry, deployed on Azure infrastructure.

## Architecture

This project demonstrates a full-stack observability solution with:

- **Frontend** (`web/`): Static Web App (React/Next.js) - User interface for interacting with the GenAI application
- **Backend** (`api/`): Function App (Python, Linux Consumption) - Azure Functions-based API layer with:
  - **Health Check Endpoint** (`/api/health`): No authentication required
  - **Chat Endpoint** (`/api/chat`): Entra ID JWT authentication
  - **Azure OpenAI Integration**: Uses DefaultAzureCredential for managed identity
  - **Optional RAG**: Query Azure AI Search and inject context into prompts
  - **OpenTelemetry**: Full instrumentation with Application Insights
  - **Stateless Design**: No database, metadata-only logging (no user content stored)
- **Infrastructure** (`infra/`): Bicep templates for Azure resource deployment
- **AI Services**: Azure AI Search, Microsoft Foundry
- **Observability**: Application Insights + Log Analytics Workspace
- **Storage**: Azure Storage Account
- **Security**: Azure Key Vault for secrets management
- **Documentation** (`docs/`): Additional project documentation

All resources are deployed to **Sweden Central** (except the resource group in Switzerland North).

## Repository Structure

```
foundry-observability-demo/
├── web/                        # Frontend application
├── api/                        # Azure Functions backend
│   ├── function_app.py        # Main functions app
│   ├── health.py              # Health check endpoint
│   ├── chat.py                # Chat endpoint with OpenAI & RAG
│   ├── auth.py                # JWT validation
│   ├── telemetry.py           # OpenTelemetry configuration
│   ├── tests/                 # Unit tests (16 tests)
│   └── README.md              # Detailed API documentation
├── infra/                      # Infrastructure as Code (Bicep)
│   ├── main.bicep             # Main Bicep template
│   ├── parameters.json        # Deployment parameters
│   ├── deploy.sh              # Automated deployment script
│   ├── .bicepconfig.json      # Bicep configuration
│   └── README.md              # Detailed infrastructure docs
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
│   └── generate-env.sh        # Generate .env from deployment
├── .env.template              # Environment variables template
├── .gitignore                 # Git ignore patterns
├── pyproject.toml             # Python linting configuration
├── LICENSE                    # License file
└── README.md                  # This file
```

## Getting Started

### Prerequisites

- Azure CLI installed and authenticated
- Azure subscription with appropriate permissions
- Python 3.11+
- Node.js 18+
- Azure Functions Core Tools (for local API development)
- Git

### Infrastructure Deployment

The infrastructure is deployed using Bicep templates. For detailed deployment instructions, see [infra/README.md](infra/README.md).

#### Quick Start

```bash
cd infra
./deploy.sh demo
```

Or manually:

```bash
cd infra
az deployment group create \
  --resource-group rg-foundry-demo \
  --template-file main.bicep \
  --parameters parameters.json
```

For complete documentation including:
- Step-by-step deployment guide
- Post-deployment configuration
- Manual steps for Foundry project creation
- Troubleshooting tips

See the comprehensive guide: **[infra/README.md](infra/README.md)**

## Infrastructure Resources

| Resource | Purpose | Location |
|----------|---------|----------|
| Resource Group | Container for all resources | Switzerland North |
| Static Web App | Frontend hosting | Sweden Central |
| Function App | Backend API (Python 3.11) | Sweden Central |
| Storage Account | Data storage | Sweden Central |
| Application Insights | Application monitoring | Sweden Central |
| Log Analytics | Centralized logging | Sweden Central |
| Azure AI Search | Search and vector store | Sweden Central |
| Key Vault | Secrets management | Sweden Central |

## Local Development Setup

### Backend (Azure Functions)

1. Navigate to the API directory:
   ```bash
   cd api/
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

4. Copy the example settings file:
   ```bash
   cp local.settings.example.json local.settings.json
   ```

5. Update `local.settings.json` with your configuration (do not commit this file)

6. Run the Azure Functions locally:
   ```bash
   func start
   ```

The API will be available at `http://localhost:7071`

For detailed API documentation, see [api/README.md](api/README.md).

### Frontend

1. Navigate to the web directory:
   ```bash
   cd web/
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

### Environment Variables

After infrastructure deployment, configure your local environment with the outputs:

```bash
# Get deployment outputs
az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs
```

Or use the provided script:

```bash
./scripts/generate-env.sh
```

Key environment variables (set in `local.settings.json` for local development):

- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_VERSION`: API version for Azure OpenAI
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Application Insights connection string
- `AZURE_SEARCH_ENDPOINT`: Azure AI Search endpoint
- `AZURE_KEY_VAULT_ENDPOINT`: Key Vault URI
- `STORAGE_ACCOUNT_NAME`: Storage account name

## API Features

The backend API provides:

- ✅ Entra ID JWT authentication with configurable issuer/audience
- ✅ Azure OpenAI integration via Foundry deployment
- ✅ Optional RAG with Azure AI Search
- ✅ Correlation IDs for request tracking
- ✅ OpenTelemetry instrumentation to Application Insights
- ✅ Stateless, metadata-only logging (no user content stored)
- ✅ Comprehensive unit tests (16 tests)
- ✅ VS Code devcontainer support

## Development Conventions

### Code Style

**Python (API)**
- Use Python 3.11+
- Follow PEP 8 style guide
- Use `ruff` for linting and `black` for code formatting
- Line length: 88 characters

**JavaScript/TypeScript (Frontend)**
- Use ESLint for linting
- Use Prettier for code formatting
- Single quotes for strings
- 2-space indentation
- Semicolons required

### Linting

**Python**
```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code with black
black .
```

**Frontend**
```bash
cd web/

# Run ESLint
npm run lint

# Auto-fix ESLint issues
npm run lint:fix

# Format with Prettier
npm run format

# Check formatting
npm run format:check
```

## Configuration

### API Configuration

Configure the Azure Functions backend by creating a `local.settings.json` file in the `api/` directory. Use `local.settings.example.json` as a template.

**Never commit `local.settings.json` to version control** - it may contain secrets.

## Deployment

### Infrastructure (Issue #B)

✅ **Completed** - Bicep templates for deploying Azure infrastructure to Sweden Central.

See [infra/README.md](infra/README.md) for deployment instructions.

### Function App (Issue #C)

✅ **Completed** - Python Function App with JWT auth, OpenAI integration, and OpenTelemetry.

Required app settings are outputted by the infrastructure deployment.

### Static Web App (Issue #3)

🔜 **Coming Soon** - Frontend deployment.

Required app settings are outputted by the infrastructure deployment.

## Manual Steps

### Microsoft Foundry Project Creation

Microsoft Foundry projects require manual creation as they are in preview and don't have stable IaC providers yet.

**Steps:**
1. Navigate to Azure Portal → Microsoft Foundry / Azure AI Studio
2. Create new project:
   - Name: `foundry-observability-demo`
   - Resource Group: `rg-foundry-demo`
   - Location: `Sweden Central`
3. Link deployed resources (App Insights, Storage, AI Search)

For detailed instructions, see the [Manual Steps section in infra/README.md](infra/README.md#manual-steps-required).

## Monitoring and Observability

All application telemetry flows to Application Insights and Log Analytics:

- **Application Insights**: Real-time monitoring, metrics, and distributed tracing
- **Log Analytics**: Centralized log aggregation and querying
- **Custom Dashboards**: (To be configured in Azure Portal)

## Security

- **Managed Identities**: Function App uses system-assigned managed identity
- **RBAC**: Least-privilege access to Key Vault and Storage
- **Secrets**: All secrets stored in Azure Key Vault
- **HTTPS Only**: All endpoints enforce HTTPS
- **TLS 1.2**: Minimum TLS version enforced
- **JWT Authentication**: Entra ID token validation for API endpoints
- **No User Content in Logs**: Metadata-only logging policy

## Contributing

1. Follow the established code style and conventions
2. Run linters before committing code
3. Ensure all tests pass
4. Keep commits focused and atomic

## License

See [LICENSE](LICENSE) file for details.

## Related Issues

- **Issue #B** (This): Bicep/IaC deployment ✅
- **Issue #C** (This): Azure Functions API ✅
- **Issue #3**: Static Web App deployment 🔜

## Support

For deployment issues, see the troubleshooting section in [infra/README.md](infra/README.md#troubleshooting).
