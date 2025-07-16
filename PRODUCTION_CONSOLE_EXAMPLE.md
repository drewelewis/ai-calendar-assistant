# Production Console Output Example

This example shows how to use the smart console output feature in your AI Calendar Assistant application.

## Quick Setup

### 1. Environment Configuration

Add these environment variables to control console output:

```bash
# Minimal production output (recommended)
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=INFO
TELEMETRY_CONSOLE_COLORS=false
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=false
```

### 2. No Code Changes Required

The console output is automatically integrated into your existing telemetry system. No code changes are needed.

### 3. What You'll See

With the above configuration, you'll see output like this in your application logs:

```
[14:23:14.998] INFO  💬 CHAT_REQUEST: session_id=session-123 message_length=45 has_cosmosdb=true
[14:23:15.001] INFO  🤖 OPENAI_CALL: model=gpt-4o operation=chat_completion
[14:23:15.123] INFO  📊 TOKEN_USAGE: model=gpt-4o operation=chat input_tokens=245 output_tokens=89 total_tokens=334 estimated_cost=$0.0053
[14:23:15.230] INFO  Telemetry configuration completed successfully
```

## Environment-Specific Configurations

### Development Environment
```bash
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=DEBUG
TELEMETRY_CONSOLE_COLORS=true
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=true
```

This provides detailed output with colors and module information for debugging.

### Production Environment
```bash
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=WARNING
TELEMETRY_CONSOLE_COLORS=false
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=false
```

This shows only warnings and errors, suitable for production monitoring.

### Container/Kubernetes Environment
```bash
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=INFO
TELEMETRY_CONSOLE_COLORS=false
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=false
```

Optimized for log aggregation systems that prefer plain text.

### Completely Disabled
```bash
TELEMETRY_CONSOLE_ENABLED=false
```

Turns off all console output while keeping telemetry data flowing to Application Insights.

## Benefits

1. **Real-time Visibility**: See token usage and costs immediately in your console
2. **No Code Changes**: Configure entirely through environment variables
3. **Performance Monitoring**: Track request latency and error rates
4. **Cost Monitoring**: Real-time cost tracking for OpenAI API calls
5. **Debug Friendly**: Detailed span information for troubleshooting
6. **Production Ready**: Configurable levels to reduce noise in production

## Monitoring in Production

The console output complements your Application Insights telemetry by providing:

- **Immediate feedback** on application behavior
- **Cost awareness** for every OpenAI API call
- **Performance insights** through span timing
- **Error visibility** without needing to check logs
- **Session tracking** for user behavior analysis

## Integration with Existing Logging

The console output works alongside your existing logging infrastructure:

- **Application Insights**: Structured telemetry data for analysis
- **Console Output**: Real-time visibility for operators
- **File Logs**: Traditional log files continue to work
- **Container Logs**: Visible in kubectl logs, docker logs, etc.

This gives you the best of both worlds: detailed analytics and immediate visibility.
