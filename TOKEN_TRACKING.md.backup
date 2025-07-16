# Token Tracking Implementation

This document describes the comprehensive token tracking system implemented for the AI Calendar Assistant, providing both per-request spans and aggregated metrics for OpenAI API usage monitoring.

## Overview

The token tracking system provides:

- **Spans**: Per-request token tracking with detailed metadata and latency information
- **Metrics**: Aggregated token usage and cost monitoring across all requests
- **Automatic Instrumentation**: Transparent tracking for Semantic Kernel OpenAI calls
- **Cost Estimation**: Real-time cost calculations based on current pricing models

## Features

### 📊 Span-Level Tracking (Per-Request)

Each OpenAI API call creates a detailed span with the following attributes:

- `openai.tokens.prompt` - Number of input tokens
- `openai.tokens.completion` - Number of output tokens  
- `openai.tokens.total` - Total tokens consumed
- `openai.model` - Model/deployment name used
- `openai.duration_ms` - Request latency in milliseconds
- `openai.cost.estimated_usd` - Estimated cost in USD
- `openai.cost.estimated_cents` - Estimated cost in cents
- `operation` - Type of operation (chat_completion, etc.)

### 📈 Aggregated Metrics

The system records the following metrics for monitoring and alerting:

- **`openai_tokens_total`** - Counter tracking total tokens by type
  - Labels: `model`, `operation`, `token_type` (total/prompt/completion), `status`
- **`openai_token_cost_total`** - Counter tracking estimated costs in cents
  - Labels: `model`, `operation`, `status`
- **`openai_request_duration_ms`** - Histogram of request latencies
  - Labels: `model`, `operation`, `status`

### 🤖 Automatic Instrumentation

Semantic Kernel OpenAI service calls are automatically instrumented without code changes:

```python
# This call is automatically tracked
response = await agent.get_response(messages=message, thread=thread)
```

## Implementation Details

### Core Components

1. **`telemetry/token_tracking.py`** - Core token tracking utilities
2. **`telemetry/semantic_kernel_instrumentation.py`** - Automatic SK instrumentation
3. **`telemetry/config.py`** - Enhanced telemetry configuration
4. **`telemetry/decorators.py`** - Existing telemetry decorators

### Token Pricing Models

The system includes current pricing for common Azure OpenAI models:

```python
TOKEN_PRICING = {
    "gpt-4o": {
        "input": 0.005,   # $0.005 per 1K input tokens
        "output": 0.015,  # $0.015 per 1K output tokens
    },
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.0006,
    },
    # ... more models
}
```

### Cost Calculation

Costs are calculated using the formula:
```
Total Cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
```

## Usage Examples

### Automatic Tracking (Recommended)

The simplest approach - just initialize telemetry and use your existing code:

```python
from telemetry import initialize_telemetry
from ai.agent import Agent

# Initialize telemetry (enables automatic tracking)
initialize_telemetry()

# All OpenAI calls are now automatically tracked
agent = Agent("session-123")
response = await agent.invoke("Hello!")  # Automatically tracked
```

### Manual Tracking with Decorator

For direct OpenAI API calls, use the tracking decorator:

```python
from telemetry import track_openai_tokens

@track_openai_tokens(model_name="gpt-4o", operation_name="custom_chat")
async def my_openai_call():
    response = await client.chat.completions.create(...)
    return response
```

### Manual Span Attributes

Add token information to existing spans:

```python
from telemetry import add_token_span_attributes, record_token_metrics

# Add to current span
add_token_span_attributes(openai_response, "gpt-4o")

# Record aggregated metrics
record_token_metrics(openai_response, "gpt-4o", "chat_completion")
```

## Monitoring and Alerting

### Azure Application Insights Queries

**View token usage by model:**
```kusto
customMetrics
| where name == "openai_tokens_total"
| summarize TotalTokens = sum(value) by tostring(customDimensions.model), bin(timestamp, 1h)
| render timechart
```

**Track costs over time:**
```kusto
customMetrics
| where name == "openai_token_cost_total"
| summarize TotalCostCents = sum(value) by bin(timestamp, 1h)
| extend TotalCostUSD = TotalCostCents / 100
| render timechart
```

**Monitor request latency:**
```kusto
customMetrics
| where name == "openai_request_duration_ms"
| summarize avg(value), percentile(value, 95) by tostring(customDimensions.model), bin(timestamp, 5m)
| render timechart
```

**Find expensive requests:**
```kusto
dependencies
| where name contains "openai"
| where customDimensions.["openai.cost.estimated_usd"] > 0.01  // Requests over 1 cent
| project timestamp, customDimensions.["openai.model"], customDimensions.["openai.tokens.total"], customDimensions.["openai.cost.estimated_usd"]
| order by timestamp desc
```

### Setting Up Alerts

Create alerts in Azure Monitor for:

1. **High Token Usage**: Alert when hourly token usage exceeds threshold
2. **Cost Monitoring**: Alert when daily costs exceed budget
3. **Error Rates**: Alert on high failure rates for OpenAI calls
4. **Latency Issues**: Alert when 95th percentile latency is too high

## Configuration

### Environment Variables

The system uses these environment variables:

- `APPLICATIONINSIGHTS_CONNECTION_STRING` - Required for telemetry
- `OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `OPENAI_API_KEY` - API key
- `OPENAI_MODEL_DEPLOYMENT_NAME` - Model deployment name

### Telemetry Settings

```python
# Initialize with custom settings
initialize_telemetry(
    service_name="ai-calendar-assistant",
    service_version="1.0.0",
    log_level=logging.INFO
)
```

## Troubleshooting

### Token Information Not Appearing

1. **Check Semantic Kernel Version**: Ensure you're using a compatible version
2. **Verify Response Structure**: Token usage might be in different response attributes
3. **Enable Debug Logging**: Set log level to DEBUG to see extraction attempts

### Cost Calculations Seem Wrong

1. **Update Pricing**: Check if pricing models in `TOKEN_PRICING` are current
2. **Model Mapping**: Ensure your deployment name maps to the correct pricing model
3. **Token Extraction**: Verify token counts are being extracted correctly

### Missing Metrics in Application Insights

1. **Connection String**: Verify `APPLICATIONINSIGHTS_CONNECTION_STRING` is set
2. **Telemetry Initialization**: Ensure `initialize_telemetry()` returns `True`
3. **Buffering**: Metrics may take a few minutes to appear in Application Insights

## Development and Testing

Run the demo to test token tracking:

```bash
python demo_token_tracking.py
```

This will:
1. Initialize telemetry
2. Create test OpenAI API calls
3. Show token tracking in action
4. Display available metrics

## Future Enhancements

Potential improvements:

1. **Real-time Pricing API**: Automatically update pricing from Azure API
2. **Budget Enforcement**: Add spending limits and automatic throttling
3. **Usage Analytics**: Dashboard showing usage patterns and optimization opportunities
4. **Model Recommendation**: Suggest optimal models based on usage patterns
