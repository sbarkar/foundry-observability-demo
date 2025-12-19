# Foundry Observability Demo

A demo application showcasing comprehensive observability for GenAI applications using OpenTelemetry and Azure Application Insights. This repository demonstrates how to instrument a RAG-powered LLM application with distributed tracing, custom events, and metrics while ensuring privacy-compliant metadata-only logging.

## Features

- ✅ **OpenTelemetry Integration**: Full distributed tracing with hierarchical spans
- ✅ **Azure Application Insights Export**: Seamless telemetry export to Azure Monitor
- ✅ **RAG Observability**: Track document retrieval, context building, and vector search
- ✅ **LLM Monitoring**: Monitor token usage, latency, and model performance
- ✅ **Safety Tracking**: Monitor content safety checks and blocked outputs
- ✅ **Privacy-First**: Metadata-only logging (no raw prompts/responses)
- ✅ **KQL Dashboards**: Pre-built queries for latency, costs, errors, and usage analysis

## Quick Start

### Prerequisites

- Python 3.8+
- Azure Application Insights resource (optional for local testing)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sbarkar/foundry-observability-demo.git
cd foundry-observability-demo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Application Insights (optional):
```bash
cp .env.example .env
# Edit .env and add your APPLICATIONINSIGHTS_CONNECTION_STRING
```

4. Run the demo application:
```bash
python -m app.main
```

## Configuration

### Environment Variables

- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Azure Application Insights connection string (optional)
  - If not set, the app runs with OpenTelemetry instrumentation but doesn't export telemetry
  - Get from: Azure Portal > Application Insights > Overview/Properties > Connection String

## Application Structure

```
foundry-observability-demo/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Main application with request handling
│   ├── observability.py      # OpenTelemetry setup and utilities
│   ├── llm.py                # LLM client with tracing
│   └── rag.py                # RAG client with document retrieval
├── docs/
│   └── observability.md      # Comprehensive observability guide with KQL queries
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
└── README.md                 # This file
```

## Observability Features

### Instrumented Operations

1. **Request Processing** (`request.process`)
   - End-to-end request tracing
   - Success/failure tracking
   - Total latency measurement

2. **RAG Operations** (`rag.retrieve`, `rag.build_context`)
   - Document retrieval metrics
   - Context building performance
   - Similarity scores

3. **LLM Calls** (`llm.call`)
   - Token usage (prompt, completion, total)
   - Model performance
   - Latency tracking

4. **Safety Checks** (`llm.safety_check`)
   - Content safety validation
   - Blocked content categories
   - Pass/fail rates

### Custom Events

- `llm.tokens`: Token consumption details
- `llm.latency`: LLM response times
- `rag.retrieval_complete`: RAG performance metrics
- `safety.check_complete`: Safety check results
- `request.complete`: Request summary
- `request.blocked`: Safety filter blocks
- `request.error`: Error details

### Metrics

- `genai.requests.total`: Total request count
- `genai.errors.total`: Error count by type
- `genai.tokens.total`: Token consumption by type and model

## Documentation

For detailed information on:
- KQL queries for dashboards
- Workbook creation
- Alert setup
- Best practices
- Troubleshooting

See: [docs/observability.md](docs/observability.md)

## Sample KQL Queries

### Latency P95 Over Time
```kql
traces
| where message == "request.complete"
| extend latency_ms = todouble(customDimensions.["request.total_latency_ms"])
| summarize p95 = percentile(latency_ms, 95) by bin(timestamp, 5m)
| render timechart
```

### Token Usage Over Time
```kql
traces
| where message == "llm.tokens"
| extend total_tokens = toint(customDimensions.["llm.usage.total_tokens"])
| summarize sum(total_tokens) by bin(timestamp, 1h)
| render timechart
```

See [docs/observability.md](docs/observability.md) for 20+ production-ready queries.

## Privacy & Security

This application demonstrates **metadata-only logging**:

✅ **Logged**: Query length, token counts, latency, model names, document counts  
❌ **NOT Logged**: Raw prompts, responses, document content, user messages

Sensitive fields are explicitly filtered in the `observability.py` module.

## Contributing

Contributions are welcome! Please ensure any instrumentation changes maintain privacy-compliant logging.

## License

MIT License - see [LICENSE](LICENSE) file for details.
