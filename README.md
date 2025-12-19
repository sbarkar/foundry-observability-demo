# Foundry Observability Demo

A comprehensive example showcasing how to use Microsoft Foundry to deploy a compliant GenAI use case with enterprise-grade observability using Microsoft native tools.

## Overview

This repository demonstrates a production-ready approach to building observable and compliant GenAI applications on Microsoft Foundry. The solution integrates:

- **Microsoft Foundry** for AI orchestration and governance
- **Azure OpenAI** for language generation
- **Azure AI Search** for document retrieval (RAG pattern)
- **Application Insights** for comprehensive telemetry
- **Azure Monitor** for dashboards, alerts, and workbooks

### Key Features

✅ **Complete Observability**: End-to-end distributed tracing from user request to AI response  
✅ **Privacy-First**: Telemetry-only approach—no user content stored by default  
✅ **Governance Controls**: Built-in content filtering, policy enforcement, and audit logging  
✅ **Azure-Native**: Uses standard Azure services (no vendor lock-in)  
✅ **Production-Ready**: Includes monitoring, alerting, and operational runbooks

## Documentation

### 📖 [Demo Script](docs/demo-script.md)
A 10-15 minute walkthrough demonstrating:
- How to navigate the Foundry Portal
- Running sample queries and viewing traces
- Deep dive into Application Insights
- Monitoring AI Search usage
- Understanding the governance posture

### 🏗️ [Architecture](docs/architecture.md)
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

## Quick Start

### Prerequisites

- Azure subscription with sufficient quota for:
  - Azure OpenAI (GPT-4 deployment)
  - Azure AI Search (Standard tier or higher)
  - Application Insights
- Azure CLI installed and authenticated
- Permissions to create resources in your subscription

### Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/sbarkar/foundry-observability-demo.git
   cd foundry-observability-demo
   ```

2. **Deploy infrastructure**
   ```bash
   # Coming soon: Infrastructure as Code templates
   # For now, see docs/demo-script.md for manual setup instructions
   ```

3. **Configure observability**
   - Create Application Insights resource
   - Link to Foundry project
   - Deploy monitoring workbooks

4. **Run the demo**
   - Follow the [Demo Script](docs/demo-script.md) for a guided walkthrough

## Governance Posture

### Telemetry-Only Approach

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

## Optional: Conversation History

By default, this solution does NOT persist conversation history. However, for use cases requiring multi-turn conversations or feedback loops, you can enable **Cosmos DB integration**.

### When to Enable Conversation History

- Multi-turn conversations requiring context
- User feedback and rating systems
- Regulatory requirements to retain records
- Debugging complex user-reported issues

### Enabling Cosmos DB

See `/infra` directory (coming soon) for:
- Cosmos DB provisioning templates
- Connection configuration for Foundry
- Data retention and purging policies
- Encryption and access control setup

**⚠️ Important:** Enabling conversation history changes your compliance posture. Consult with legal and security teams before enabling in production.

## Architecture Highlights

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   User      │────────▶│  Microsoft       │────────▶│  Azure OpenAI   │
│   Request   │         │  Foundry         │         │  + AI Search    │
└─────────────┘         └──────────────────┘         └─────────────────┘
                               │
                               │ Telemetry
                               │ (No Content)
                               ▼
                        ┌──────────────────┐
                        │  Application     │
                        │  Insights        │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Azure Monitor   │
                        │  Workbooks       │
                        │  Alerts          │
                        └──────────────────┘
```

For detailed architecture diagrams, see [docs/architecture.md](docs/architecture.md).

## Cost Estimation

Approximate monthly costs (assuming moderate usage):

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| Azure OpenAI | GPT-4, ~1M tokens/month | $30 |
| Azure AI Search | Standard tier | $250 |
| Application Insights | 5GB/month | $10 |
| Log Analytics | 5GB/month | $10 |
| Cosmos DB (optional) | Provisioned throughput | $25 |
| **Total (without Cosmos DB)** | | **~$300/month** |

*Costs vary based on region, usage patterns, and retention policies.*

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
- **Issues**: [GitHub Issues](https://github.com/sbarkar/foundry-observability-demo/issues)
- **Documentation**: See `/docs` directory
- **Azure Support**: [Azure Support Portal](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

## Additional Resources

- [Microsoft Foundry Documentation](https://foundry.microsoft.com/docs)
- [Azure OpenAI Service](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Azure AI Search](https://docs.microsoft.com/azure/search/)
- [Application Insights](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Azure Monitor](https://docs.microsoft.com/azure/azure-monitor/)

---

**Built with ❤️ using Microsoft Azure and Foundry**
