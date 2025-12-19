# Observability with OpenTelemetry and Application Insights

This document describes the observability setup for the Foundry GenAI Demo application, including OpenTelemetry instrumentation, Azure Application Insights integration, and sample KQL queries for monitoring and dashboarding.

## Overview

The application uses OpenTelemetry to instrument:
- **Request traces**: End-to-end request processing
- **RAG operations**: Document retrieval and context building
- **LLM calls**: Language model interactions with token usage
- **Safety checks**: Content safety validation
- **Custom events**: Token usage, latency metrics, safety blocks, and errors

All telemetry is exported to Azure Application Insights for visualization and analysis.

## Configuration

### Environment Variables

Set the following environment variable to enable telemetry export:

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=<your_connection_string>
```

Get your connection string from:
1. Navigate to your Application Insights resource in Azure Portal
2. Go to "Overview" or "Properties"
3. Copy the "Connection String"

The format looks like:
```
InstrumentationKey=<key>;IngestionEndpoint=https://<region>.in.applicationinsights.azure.com/
```

### Local Development

If `APPLICATIONINSIGHTS_CONNECTION_STRING` is not set, the application will still run with OpenTelemetry instrumentation but won't export telemetry to Azure. This is useful for local development.

## Instrumentation Details

### Spans Hierarchy

The application creates a hierarchical span structure for each request:

```
request.process (root span)
├── request.rag_phase (if RAG is enabled)
│   ├── rag.retrieve
│   └── rag.build_context
├── request.safety_check
│   └── llm.safety_check
├── request.llm_phase
│   └── llm.call
└── request.response_generation
```

### Span Attributes

All spans include metadata attributes (no sensitive data):

- **Request spans**: `request.query_length`, `request.use_rag`, `request.timestamp`
- **RAG spans**: `rag.query_length`, `rag.top_k`, `rag.documents_retrieved`, `rag.latency_ms`
- **LLM spans**: `llm.model`, `llm.max_tokens`, `llm.prompt_length`, `llm.latency_ms`
- **Safety spans**: `safety.is_safe`, `safety.blocked`, `safety.result`

### Custom Events

Custom events track important metrics:

- `llm.tokens`: Token usage (prompt, completion, total)
- `llm.latency`: LLM call latency
- `rag.retrieval_complete`: RAG retrieval metrics
- `safety.check_complete`: Safety check results
- `request.complete`: Request completion summary
- `request.blocked`: Content safety blocks
- `request.error`: Error details

### Metrics

Counters track aggregate statistics:

- `genai.requests.total`: Total requests processed
- `genai.errors.total`: Total errors encountered
- `genai.tokens.total`: Total tokens consumed (by type: prompt, completion, total)

## Privacy and Security

**Important**: The instrumentation is designed for metadata-only logging:

- ✅ Logged: Query length, token counts, latency, model names, document counts
- ❌ NOT logged: Raw prompts, responses, document content, user messages

Sensitive fields (`prompt`, `response`, `raw_text`, `content`, `message`) are explicitly filtered out in the `observability.py` module.

## KQL Queries for Application Insights

Use these queries in Application Insights > Logs or create dashboards/workbooks with them.

### 1. Request Latency Analysis

#### P95 Latency Over Time
```kql
traces
| where message == "request.complete"
| extend latency_ms = todouble(customDimensions.["request.total_latency_ms"])
| summarize 
    p50 = percentile(latency_ms, 50),
    p95 = percentile(latency_ms, 95),
    p99 = percentile(latency_ms, 99),
    avg = avg(latency_ms),
    count = count()
    by bin(timestamp, 5m)
| render timechart
```

#### Latency Distribution
```kql
traces
| where message == "request.complete"
| extend latency_ms = todouble(customDimensions.["request.total_latency_ms"])
| summarize count() by bin(latency_ms, 100)
| render columnchart
```

### 2. Token Usage Tracking

#### Total Tokens Over Time
```kql
traces
| where message == "llm.tokens"
| extend 
    prompt_tokens = toint(customDimensions.["llm.usage.prompt_tokens"]),
    completion_tokens = toint(customDimensions.["llm.usage.completion_tokens"]),
    total_tokens = toint(customDimensions.["llm.usage.total_tokens"])
| summarize 
    total_prompt = sum(prompt_tokens),
    total_completion = sum(completion_tokens),
    total = sum(total_tokens)
    by bin(timestamp, 1h)
| render timechart
```

#### Token Usage by Request
```kql
traces
| where message == "llm.tokens"
| extend 
    total_tokens = toint(customDimensions.["llm.usage.total_tokens"])
| summarize 
    avg_tokens = avg(total_tokens),
    max_tokens = max(total_tokens),
    min_tokens = min(total_tokens),
    count = count()
| project avg_tokens, max_tokens, min_tokens, count
```

#### Cost Estimation (GPT-4)
```kql
// Assuming GPT-4 pricing: $0.03 per 1K prompt tokens, $0.06 per 1K completion tokens
traces
| where message == "llm.tokens"
| extend 
    prompt_tokens = toint(customDimensions.["llm.usage.prompt_tokens"]),
    completion_tokens = toint(customDimensions.["llm.usage.completion_tokens"])
| extend 
    prompt_cost = (prompt_tokens / 1000.0) * 0.03,
    completion_cost = (completion_tokens / 1000.0) * 0.06,
    total_cost = ((prompt_tokens / 1000.0) * 0.03) + ((completion_tokens / 1000.0) * 0.06)
| summarize 
    total_prompt_cost = sum(prompt_cost),
    total_completion_cost = sum(completion_cost),
    total_cost = sum(total_cost),
    total_requests = count()
    by bin(timestamp, 1d)
| render timechart
```

### 3. RAG Usage Analysis

#### RAG vs Non-RAG Requests
```kql
dependencies
| where name == "request.process"
| extend use_rag = tobool(customDimensions.["request.use_rag"])
| summarize count() by use_rag, bin(timestamp, 1h)
| render timechart
```

#### RAG Performance Metrics
```kql
traces
| where message == "rag.retrieval_complete"
| extend 
    docs_retrieved = toint(customDimensions.["rag.documents_retrieved"]),
    avg_similarity = todouble(customDimensions.["rag.avg_similarity"]),
    latency_ms = todouble(customDimensions.["rag.latency_ms"])
| summarize 
    avg_docs = avg(docs_retrieved),
    avg_similarity = avg(avg_similarity),
    avg_latency = avg(latency_ms)
    by bin(timestamp, 15m)
| render timechart
```

#### RAG Document Retrieval Distribution
```kql
traces
| where message == "rag.retrieval_complete"
| extend docs_retrieved = toint(customDimensions.["rag.documents_retrieved"])
| summarize count() by docs_retrieved
| render piechart
```

### 4. Error and Failure Analysis

#### Error Rate Over Time
```kql
traces
| where message == "request.error" or message contains "error"
| extend error_type = tostring(customDimensions.["error.type"])
| summarize error_count = count() by bin(timestamp, 5m), error_type
| render timechart
```

#### Errors by Type
```kql
traces
| where message == "request.error"
| extend 
    error_type = tostring(customDimensions.["error.type"]),
    error_message = tostring(customDimensions.["error.message"])
| summarize count() by error_type
| order by count_ desc
```

#### Success vs Failure Rate
```kql
traces
| where message == "request.complete" or message == "request.error"
| extend is_success = iff(message == "request.complete", "success", "failure")
| summarize count() by is_success, bin(timestamp, 5m)
| render timechart
```

### 5. Safety and Content Filtering

#### Safety Blocks Over Time
```kql
traces
| where message == "request.blocked" or message == "safety.check_complete"
| extend 
    is_blocked = tobool(customDimensions.["safety.blocked"])
| where is_blocked == true
| summarize blocked_count = count() by bin(timestamp, 1h)
| render timechart
```

#### Blocked Content Categories
```kql
traces
| where message == "request.blocked"
| extend blocked_categories = tostring(customDimensions.["blocked_categories"])
| extend category = split(blocked_categories, ",")
| mv-expand category
| summarize count() by tostring(category)
| render piechart
```

#### Safety Check Pass Rate
```kql
traces
| where message == "safety.check_complete"
| extend is_safe = tobool(customDimensions.["safety.is_safe"])
| summarize 
    total = count(),
    passed = countif(is_safe == true),
    blocked = countif(is_safe == false)
    by bin(timestamp, 1h)
| extend pass_rate = (todouble(passed) / todouble(total)) * 100
| project timestamp, pass_rate, total, passed, blocked
| render timechart
```

### 6. LLM Performance Monitoring

#### LLM Call Latency
```kql
traces
| where message == "llm.latency"
| extend latency_ms = todouble(customDimensions.["llm.latency_ms"])
| summarize 
    p50 = percentile(latency_ms, 50),
    p95 = percentile(latency_ms, 95),
    p99 = percentile(latency_ms, 99)
    by bin(timestamp, 5m)
| render timechart
```

#### LLM Model Usage
```kql
dependencies
| where name == "llm.call"
| extend model = tostring(customDimensions.["llm.model"])
| summarize count() by model, bin(timestamp, 1h)
| render timechart
```

### 7. End-to-End Request Analysis

#### Request Volume
```kql
traces
| where message == "request.complete"
| summarize request_count = count() by bin(timestamp, 5m)
| render timechart
```

#### Comprehensive Request Dashboard
```kql
traces
| where message == "request.complete"
| extend 
    latency_ms = todouble(customDimensions.["request.total_latency_ms"]),
    total_tokens = toint(customDimensions.["request.total_tokens"]),
    success = tobool(customDimensions.["request.success"])
| summarize 
    request_count = count(),
    avg_latency = avg(latency_ms),
    p95_latency = percentile(latency_ms, 95),
    total_tokens = sum(total_tokens),
    success_rate = (countif(success == true) * 100.0) / count()
    by bin(timestamp, 15m)
| render timechart
```

## Creating Dashboards

### Option 1: Azure Workbook

1. Go to Application Insights > Workbooks
2. Create a new workbook
3. Add query tiles using the KQL queries above
4. Arrange tiles in a meaningful layout
5. Save and share the workbook

### Option 2: Azure Dashboard

1. Go to Azure Portal > Dashboard
2. Add "Logs" tiles
3. Paste KQL queries from above
4. Customize visualization types (chart, table, etc.)
5. Save dashboard

### Recommended Workbook Structure

**Page 1: Overview**
- Request volume (5-min bins)
- Success vs failure rate
- P95 latency
- Total token usage

**Page 2: Performance**
- Latency distribution
- LLM call latency
- RAG retrieval latency
- Latency percentiles (p50, p95, p99)

**Page 3: Usage & Cost**
- Token usage over time
- Token usage by type (prompt vs completion)
- Cost estimation
- Requests by model

**Page 4: Safety & Compliance**
- Safety check pass rate
- Blocked content over time
- Blocked categories breakdown
- Safety-related errors

**Page 5: Errors & Debugging**
- Error rate over time
- Errors by type
- Failed requests details
- Recent errors table

## Best Practices

1. **Set up alerts**: Create Azure Monitor alerts for:
   - High error rates (> 5%)
   - High latency (p95 > threshold)
   - High token consumption
   - Safety blocks spike

2. **Regular monitoring**: Review dashboards daily/weekly for:
   - Performance degradation
   - Cost trends
   - Error patterns
   - Safety issues

3. **Retention**: Configure Application Insights data retention based on compliance needs

4. **Sampling**: For high-volume applications, consider configuring sampling in OpenTelemetry to reduce costs

5. **Privacy**: Always verify that sensitive data (prompts, responses) is not being logged

## Troubleshooting

### Telemetry not appearing in Application Insights

1. Verify `APPLICATIONINSIGHTS_CONNECTION_STRING` is set correctly
2. Check network connectivity to Azure
3. Look for export errors in application logs
4. Verify Application Insights resource is active

### Incomplete traces

1. Ensure all spans are properly closed
2. Check for exceptions during span creation
3. Verify BatchSpanProcessor is flushing before app exit

### High data volume

1. Enable sampling in OpenTelemetry SDK
2. Reduce event frequency for high-frequency operations
3. Consider using metrics instead of events for some data points

## Additional Resources

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Azure Monitor OpenTelemetry Exporter](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/monitor/azure-monitor-opentelemetry-exporter)
- [KQL Quick Reference](https://docs.microsoft.com/en-us/azure/data-explorer/kql-quick-reference)
- [Application Insights Overview](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
