# OpenTelemetry Integration with Azure Monitor

This document explains the OpenTelemetry implementation for the AI Calendar Assistant, providing comprehensive observability through Azure Application Insights.

## Overview

The application now includes:
- **Distributed Tracing** - Track requests across services and dependencies
- **Metrics Collection** - Monitor performance, usage, and custom business metrics
- **Structured Logging** - Centralized logging with correlation IDs
- **Azure Service Instrumentation** - Automatic tracking of Azure OpenAI, CosmosDB, and Microsoft Graph calls

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  OpenTelemetry   │───▶│ Azure Monitor   │
│                 │    │   Telemetry      │    │ (App Insights)  │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • HTTP requests │    │ • Traces         │    │ • Application   │
│ • Agent calls   │    │ • Metrics        │    │   Map           │
│ • Azure APIs    │    │ • Logs           │    │ • Live Metrics  │
│ • CosmosDB      │    │ • Correlation    │    │ • Query logs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Application Insights connection string (required)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key;IngestionEndpoint=https://region.in.applicationinsights.azure.com/

# Optional telemetry configuration
TELEMETRY_SERVICE_NAME=ai-calendar-assistant
TELEMETRY_SERVICE_VERSION=1.0.0
ENVIRONMENT=development
```

### Setup Application Insights

1. **Automatic Setup** (Recommended):
   ```cmd
   _setup_application_insights.bat
   ```

2. **Manual Setup**:
   ```bash
   # Create Application Insights instance
   az monitor app-insights component create \
     --app ai-calendar-assistant-insights \
     --location eastus \
     --resource-group your-resource-group \
     --application-type web
   
   # Get connection string
   az monitor app-insights component show \
     --app ai-calendar-assistant-insights \
     --resource-group your-resource-group \
     --query "connectionString" -o tsv
   ```

## Telemetry Features

### 1. Distributed Tracing

**Automatic Instrumentation:**
- HTTP requests (FastAPI, httpx, requests)
- Azure SDK calls (OpenAI, CosmosDB, Graph API)
- Database operations

**Custom Traces:**
```python
from telemetry.decorators import trace_async_method

@trace_async_method(operation_name="custom.operation")
async def my_function():
    # Your code here
    pass
```

**Manual Span Creation:**
```python
from telemetry.config import get_tracer

tracer = get_tracer()
with tracer.start_as_current_span("custom-operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Your code here
```

### 2. Metrics Collection

**Built-in Metrics:**
- `chat_requests_total` - Total chat requests processed
- `chat_request_duration_ms` - Request processing time
- `openai_api_calls_total` - OpenAI API calls
- `cosmosdb_operations_total` - CosmosDB operations
- `graph_api_calls_total` - Microsoft Graph API calls
- `active_sessions` - Current active sessions
- `memory_usage_bytes` - Application memory usage

**Custom Metrics:**
```python
from telemetry.decorators import record_metric

# Record a counter metric
record_metric("custom_events_total", 1, {"event_type": "login"})

# Using decorators
@measure_performance("my_operation")
async def my_function():
    # Automatically measures duration
    pass
```

### 3. Structured Logging

**Automatic Correlation:**
All logs include trace and span IDs for correlation:

```python
from telemetry.config import get_logger

logger = get_logger()
logger.info("Processing request", extra={"user_id": "123", "session_id": session_id})
```

**Log Levels and Context:**
```python
from telemetry.decorators import log_with_trace

log_with_trace("info", "Operation completed", operation="chat", duration_ms=150)
```

### 4. Performance Monitoring

**Method Performance:**
```python
@measure_performance("database_operation", {"table": "users"})
async def save_user(user_data):
    # Automatically records duration and success/error metrics
    pass
```

**Context Attributes:**
```python
from telemetry.decorators import TelemetryContext

with TelemetryContext(user_id="123", operation="calendar_sync"):
    # All operations within this context include these attributes
    await sync_calendar()
```

## Instrumented Components

### 1. Agent Class (`ai/agent.py`)
- Constructor initialization tracking
- Chat request processing
- OpenAI API call monitoring
- CosmosDB operation tracking
- Error handling and recovery

### 2. FastAPI Application (`api/main.py`)
- HTTP request/response tracking
- Endpoint performance monitoring
- CORS and middleware instrumentation
- Health check monitoring

### 3. Azure Services
- **Azure OpenAI**: Request tracking, token usage, model performance
- **CosmosDB**: Query performance, connection health, operation success rates
- **Microsoft Graph**: API call monitoring, authentication tracking

## Viewing Telemetry Data

### Azure Portal

1. **Application Map**: Visualize service dependencies and call flows
   - Navigate to: Application Insights → Application map
   - View real-time topology and performance

2. **Live Metrics**: Real-time performance monitoring
   - Navigate to: Application Insights → Live Metrics
   - Monitor requests, dependencies, and exceptions in real-time

3. **Transaction Search**: Find specific requests and traces
   - Navigate to: Application Insights → Transaction search
   - Search by operation, time range, or properties

4. **Performance**: Analyze slow operations
   - Navigate to: Application Insights → Performance
   - Identify bottlenecks and optimization opportunities

5. **Failures**: Monitor and analyze errors
   - Navigate to: Application Insights → Failures
   - View exception details and failure patterns

6. **Logs**: Query telemetry data with KQL
   - Navigate to: Application Insights → Logs
   - Write custom queries for detailed analysis

### Sample KQL Queries

**Chat Request Performance:**
```kql
requests
| where name == "POST /agent_chat"
| summarize avg(duration), count() by bin(timestamp, 5m)
| render timechart
```

**OpenAI API Call Success Rate:**
```kql
dependencies
| where target contains "openai.azure.com"
| summarize successRate = avg(todouble(success)) by bin(timestamp, 1h)
| render timechart
```

**Error Analysis:**
```kql
exceptions
| where timestamp > ago(24h)
| summarize count() by type, outerMessage
| order by count_ desc
```

**Custom Metrics:**
```kql
customMetrics
| where name == "chat_requests_total"
| summarize sum(value) by bin(timestamp, 1h)
| render timechart
```

## Best Practices

### 1. Trace Naming
- Use consistent naming: `service.operation` format
- Include meaningful context in span names
- Avoid high-cardinality attributes

### 2. Metric Design
- Use counters for events that increase over time
- Use histograms for durations and sizes
- Include relevant dimensions but avoid high cardinality

### 3. Logging Strategy
- Use structured logging with consistent field names
- Include correlation IDs for request tracking
- Log at appropriate levels (ERROR for failures, INFO for major operations)

### 4. Performance Considerations
- Sampling: Configure trace sampling for high-volume applications
- Batching: Telemetry is batched automatically
- Resource limits: Monitor memory usage of telemetry components

## Troubleshooting

### Connection Issues
```bash
# Test connection string
az monitor app-insights component show --app your-app-name --resource-group your-rg
```

### Missing Telemetry
- Verify `APPLICATIONINSIGHTS_CONNECTION_STRING` is set
- Check managed identity permissions for Azure-hosted applications
- Review application logs for telemetry initialization errors

### High Telemetry Volume
- Configure sampling in telemetry configuration
- Review metric cardinality
- Optimize trace attribute usage

### Authentication Issues
- Ensure managed identity has "Monitoring Metrics Publisher" role
- For local development, verify Azure CLI authentication: `az account show`

## Security Considerations

### Managed Identity (Production)
- Use managed identity for credential-less authentication
- Assign minimal required permissions
- Monitor access through Azure Activity Log

### Data Privacy
- Avoid logging sensitive data (passwords, tokens, PII)
- Use attribute filtering for sensitive span attributes
- Configure data retention policies

### Network Security
- Telemetry uses HTTPS for all communication
- Consider private endpoints for enhanced security
- Monitor network traffic patterns

## Advanced Configuration

### Custom Exporters
```python
from telemetry.config import TelemetryConfig

# Create custom configuration
telemetry = TelemetryConfig(
    service_name="my-service",
    enable_logging=True,
    enable_metrics=True,
    enable_tracing=True,
    log_level="INFO"
)
```

### Sampling Configuration
```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Configure 10% sampling
sampler = TraceIdRatioBased(0.1)
```

### Custom Resource Attributes
```python
from opentelemetry.sdk.resources import Resource

resource = Resource.create({
    "service.name": "ai-calendar-assistant",
    "service.version": "1.0.0",
    "deployment.environment": "production",
    "azure.region": "eastus"
})
```

## Monitoring Checklist

- [ ] Application Insights instance created
- [ ] Connection string configured in `.env`
- [ ] Managed identity permissions assigned
- [ ] Required packages installed
- [ ] Telemetry initialization successful
- [ ] Custom metrics working
- [ ] Traces appearing in Application Insights
- [ ] Logs correlated with traces
- [ ] Alerts configured for critical metrics
- [ ] Dashboards created for monitoring

For additional support, refer to the [Azure Monitor OpenTelemetry documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable).
