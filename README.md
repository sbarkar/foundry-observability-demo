# Foundry Observability Demo

A repository showcasing an example of how to use Microsoft Foundry to deploy a simple and compliant GenAI use case using Microsoft native tools.

## Overview

This project demonstrates observability and monitoring best practices for GenAI applications built with Microsoft Foundry, deployed on Azure infrastructure.

## Architecture

The solution consists of:

- **Frontend**: Static Web App (React/Next.js)
- **Backend**: Function App (Python, Linux Consumption)
- **AI Services**: Azure AI Search, Microsoft Foundry
- **Observability**: Application Insights, Log Analytics Workspace
- **Storage**: Azure Storage Account
- **Security**: Azure Key Vault for secrets management

All resources are deployed to **Sweden Central** (except the resource group in Switzerland North).

## Getting Started

### Prerequisites

- Azure CLI installed and authenticated
- Azure subscription with appropriate permissions
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

## Project Structure

```
foundry-observability-demo/
├── infra/                      # Infrastructure as Code (Bicep)
│   ├── main.bicep             # Main Bicep template
│   ├── parameters.json        # Deployment parameters
│   ├── deploy.sh              # Automated deployment script
│   ├── .bicepconfig.json      # Bicep configuration
│   └── README.md              # Detailed infrastructure docs
├── .gitignore                 # Git ignore patterns
├── LICENSE                    # License file
└── README.md                  # This file
```

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

## Development

### Local Development Setup

(To be added in future issues)

### Environment Variables

After infrastructure deployment, configure your local environment with the outputs:

```bash
# Get deployment outputs
az deployment group show \
  --resource-group rg-foundry-demo \
  --name main \
  --query properties.outputs
```

## Deployment

### Infrastructure (Issue #B)

✅ **Completed** - Bicep templates for deploying Azure infrastructure to Sweden Central.

See [infra/README.md](infra/README.md) for deployment instructions.

### Function App (Issue #7)

🔜 **Coming Soon** - Python Function App deployment.

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

## Contributing

(To be added)

## License

See [LICENSE](LICENSE) file for details.

## Related Issues

- **Issue #B** (This): Bicep/IaC deployment ✅
- **Issue #3**: Static Web App deployment 🔜
- **Issue #7**: Function App implementation 🔜

## Support

For deployment issues, see the troubleshooting section in [infra/README.md](infra/README.md#troubleshooting).
