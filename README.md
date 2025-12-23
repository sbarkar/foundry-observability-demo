# Foundry Observability Demo

A repository showcasing an example of how to use Microsoft Foundry to deploy a simple and compliant GenAI use case using Microsoft native tools with comprehensive observability and monitoring.
## Overview

This project demonstrates observability and monitoring best practices for GenAI applications built with Microsoft Foundry, deployed on Azure infrastructure. It includes full OpenTelemetry instrumentation, Application Insights integration, and production-ready KQL queries for monitoring.

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
- **Observability**: Application Insights + Log Analytics Workspace with custom dashboards
- **Storage**: Azure Storage Account
- **Security**: Azure Key Vault for secrets management
- **Documentation** (`docs/`): Comprehensive observability guide with KQL queries and demo walkthroughs

All resources are deployed to **Sweden Central** (except the resource group in Switzerland North).

## Key Features

- ✅ **OpenTelemetry Integration**: Full distributed tracing with hierarchical spans
- ✅ **Azure Application Insights**: Seamless telemetry export to Azure Monitor
- ✅ **RAG Observability**: Track document retrieval, context building, and vector search
- ✅ **LLM Monitoring**: Monitor token usage, latency, and model performance
- ✅ **Safety Tracking**: Monitor content safety checks and blocked outputs
- ✅ **Privacy-First**: Metadata-only logging (no raw prompts/responses)
- ✅ **KQL Dashboards**: 20+ production-ready queries for latency, costs, errors, and usage analysis
- ✅ **Entra ID Authentication**: JWT validation for secure API access
- ✅ **Infrastructure as Code**: Automated Bicep deployment
- ✅ **Demo Documentation**: Step-by-step walkthroughs and operational runbooks

## Documentation

### 📖 [Demo Script](docs/demo-script.md)
A 10-15 minute walkthrough demonstrating:
- How to navigate the Foundry Portal
- Running sample queries and viewing traces
- Deep dive into Application Insights
- Monitoring AI Search usage
- Understanding the governance posture

### 🏗️ [Architecture Diagrams](docs/architecture.md)
Detailed architecture diagrams including:
- System architecture overview
- Request flow sequences
- Telemetry data flow
- Security & compliance architecture
- Deployment and scaling patterns

### 📋 [Operational Runbook](docs/runbook.md)
Day-to-day operational procedures:
- System health checks
- Alert response procedures
- Common issues and resolutions
- Monitoring queries (KQL examples)
- Escalation procedures

### 📊 [Observability Guide](docs/observability.md)
Complete KQL query library and best practices:
- Latency analysis (p50, p95, p99)
- Token usage and cost estimation
- RAG performance metrics
- Error tracking and debugging
- Dashboard creation guide

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
│   ├── observability.md       # Observability guide with KQL queries
│   ├── demo-script.md         # 10-15 min demo walkthrough
│   ├── architecture.md        # Architecture diagrams
│   ├── runbook.md             # Operational procedures
│   └── README.md              # Documentation index
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

### Running the Demo

After infrastructure deployment, follow the **[Demo Script](docs/demo-script.md)** for a guided 10-15 minute walkthrough of:
- Navigating the Foundry Portal
- Testing the chat endpoint
- Viewing distributed traces in Application Insights
- Analyzing AI Search usage metrics
- Understanding the governance posture

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

## Observability & Monitoring

### OpenTelemetry Instrumentation

The API includes comprehensive OpenTelemetry instrumentation for:

1. **Request Processing** - End-to-end request tracing with correlation IDs
2. **RAG Operations** - Document retrieval and context building metrics
3. **LLM Calls** - Token usage, latency, and model performance tracking
4. **Safety Checks** - Content safety validation and blocked content monitoring
5. **Error Tracking** - Detailed error logging with type and message

### Span Hierarchy

```
request.process (root span)
├── request.rag_phase (if RAG enabled)
│   ├── rag.retrieve
│   └── rag.build_context
├── request.safety_check
│   └── llm.safety_check
├── request.llm_phase
│   └── llm.call
└── request.response_generation
```

### Custom Events

- `llm.tokens`: Token usage (prompt, completion, total)
- `llm.latency`: LLM call latency
- `rag.retrieval_complete`: RAG retrieval metrics
- `safety.check_complete`: Safety check results
- `request.complete`: Request completion summary
- `request.blocked`: Content safety blocks
- `request.error`: Error details

### Metrics

- `genai.requests.total`: Total requests processed
- `genai.errors.total`: Total errors encountered
- `genai.tokens.total`: Total tokens consumed (by type)

### KQL Queries & Dashboards

The project includes 20+ production-ready KQL queries for:
- Latency analysis (p50, p95, p99)
- Token usage and cost estimation
- RAG performance metrics
- Error tracking and debugging
- Safety check monitoring
- Request volume and success rates

See **[docs/observability.md](docs/observability.md)** for:
- Complete KQL query library
- Dashboard creation guide
- Alert setup recommendations
- Best practices and troubleshooting

### Sample Queries

**Latency P95 Over Time**
```kql
traces
| where message == "request.complete"
| extend latency_ms = todouble(customDimensions.["request.total_latency_ms"])
| summarize p95 = percentile(latency_ms, 95) by bin(timestamp, 5m)
| render timechart
```

**Token Usage Over Time**
```kql
traces
| where message == "llm.tokens"
| extend total_tokens = toint(customDimensions.["llm.usage.total_tokens"])
| summarize sum(total_tokens) by bin(timestamp, 1h)
| render timechart
```

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

## Privacy & Security

This application demonstrates **metadata-only logging** with a privacy-first approach:

✅ **Logged**: Query length, token counts, latency, model names, document counts, correlation IDs  
❌ **NOT Logged**: Raw prompts, responses, document content, user messages

### Governance Posture

This solution adopts a **privacy-first, compliance-friendly** approach:

- **No Content Storage**: User prompts, AI responses, and document snippets are NOT logged
- **Metadata Only**: We collect operational telemetry (latency, token counts, status codes)
- **Audit Trail**: Complete record of WHO accessed WHAT and WHEN—without WHAT was said
- **Compliance**: Aligns with GDPR, CCPA, HIPAA, and other privacy regulations

**What We Capture:**
- Request timestamps and duration
- User identity (Azure AD principal)
- Model parameters (temperature, max tokens)
- Token usage and costs
- HTTP status codes and error types
- Dependency call success/failure

**What We DON'T Capture:**
- User prompt text
- AI-generated responses
- Search query terms
- Document content from search results

This approach ensures that even if monitoring systems are compromised, no sensitive user data is exposed.

### Security Features

- **Managed Identities**: Function App uses system-assigned managed identity
- **RBAC**: Least-privilege access to Key Vault and Storage
- **Secrets**: All secrets stored in Azure Key Vault
- **HTTPS Only**: All endpoints enforce HTTPS
- **TLS 1.2**: Minimum TLS version enforced
- **JWT Authentication**: Entra ID token validation for API endpoints
- **No User Content in Logs**: Metadata-only logging policy

Sensitive fields are explicitly filtered in the telemetry module.

### Optional: Conversation History

By default, this solution does NOT persist conversation history. However, for use cases requiring multi-turn conversations or feedback loops, you can enable **Cosmos DB integration**.

**When to Enable:**
- Multi-turn conversations requiring context
- User feedback and rating systems
- Regulatory requirements to retain records
- Debugging complex user-reported issues

See [docs/demo-script.md](docs/demo-script.md#optional-conversation-history-with-cosmos-db) and the `/infra` directory for Cosmos DB provisioning templates, connection configuration, data retention policies, and encryption setup.

**⚠️ Important:** Enabling conversation history changes your compliance posture. Consult with legal and security teams before enabling in production.

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

## Deployment

### Infrastructure (Issue #B)

✅ **Completed** - Bicep templates for deploying Azure infrastructure to Sweden Central.

See [infra/README.md](infra/README.md) for deployment instructions.

### Function App (Issue #C)

✅ **Completed** - Python Function App with JWT auth, OpenAI integration, and OpenTelemetry.

Required app settings are outputted by the infrastructure deployment.

### Observability (Issue #D)

✅ **Completed** - OpenTelemetry instrumentation, Application Insights integration, and KQL dashboards.

See [docs/observability.md](docs/observability.md) for monitoring and query documentation.

### Demo Documentation (Issue #F)

✅ **Completed** - Comprehensive demo script, architecture diagrams, and operational runbooks.

See [docs/demo-script.md](docs/demo-script.md), [docs/architecture.md](docs/architecture.md), and [docs/runbook.md](docs/runbook.md) for complete documentation.

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

## Contributing

1. Follow the established code style and conventions
2. Run linters before committing code
3. Ensure all tests pass
4. Keep commits focused and atomic
5. Maintain privacy-compliant logging in all instrumentation

## License

See [LICENSE](LICENSE) file for details.

## Related Issues

- **Issue #B**: Bicep/IaC deployment ✅
- **Issue #C**: Azure Functions API ✅
- **Issue #D**: Observability & Monitoring ✅
- **Issue #F**: Demo script, architecture & runbook docs ✅
- **Issue #3**: Static Web App deployment 🔜

## Support

For deployment issues, see the troubleshooting section in [infra/README.md](infra/README.md#troubleshooting).  
For observability questions, see [docs/observability.md](docs/observability.md).  
For demo walkthrough, see [docs/demo-script.md](docs/demo-script.md).

## Additional Resources

- [Microsoft Foundry Documentation](https://foundry.microsoft.com/docs)
- [Azure OpenAI Service](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Azure AI Search](https://docs.microsoft.com/azure/search/)
- [Application Insights](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Azure Monitor](https://docs.microsoft.com/azure/azure-monitor/)
