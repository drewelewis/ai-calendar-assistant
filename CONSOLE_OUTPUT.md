# Console Output Configuration for Telemetry

This document explains how to configure the smart console output for telemetry events.

## Environment Variables

### TELEMETRY_CONSOLE_ENABLED
- **Default:** `true`
- **Description:** Enable or disable all console output
- **Example:** `TELEMETRY_CONSOLE_ENABLED=false`

### TELEMETRY_CONSOLE_LEVEL
- **Default:** `INFO`
- **Options:** `DISABLED`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `TRACE`
- **Description:** Set the minimum level for console output
- **Example:** `TELEMETRY_CONSOLE_LEVEL=DEBUG`

### TELEMETRY_CONSOLE_COLORS
- **Default:** `true`
- **Description:** Enable colored console output
- **Example:** `TELEMETRY_CONSOLE_COLORS=false`

### TELEMETRY_CONSOLE_TIMESTAMP
- **Default:** `true`
- **Description:** Include timestamps in console output
- **Example:** `TELEMETRY_CONSOLE_TIMESTAMP=false`

### TELEMETRY_CONSOLE_MODULE
- **Default:** `false`
- **Description:** Include module name in console output
- **Example:** `TELEMETRY_CONSOLE_MODULE=true`

## Configuration Examples

### Production (Minimal Output)
```bash
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=WARNING
TELEMETRY_CONSOLE_COLORS=false
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=false
```

### Development (Detailed Output)
```bash
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=DEBUG
TELEMETRY_CONSOLE_COLORS=true
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=true
```

### Debug (Maximum Output)
```bash
TELEMETRY_CONSOLE_ENABLED=true
TELEMETRY_CONSOLE_LEVEL=TRACE
TELEMETRY_CONSOLE_COLORS=true
TELEMETRY_CONSOLE_TIMESTAMP=true
TELEMETRY_CONSOLE_MODULE=true
```

### Disabled (No Console Output)
```bash
TELEMETRY_CONSOLE_ENABLED=false
```

## Sample Output

### Token Usage (INFO level)
```
[14:23:15.123] INFO  📊 TOKEN_USAGE: model=gpt-4o operation=chat input_tokens=245 output_tokens=89 total_tokens=334 estimated_cost=$0.0053
```

### OpenAI Call (INFO level)
```
[14:23:15.001] INFO  🤖 OPENAI_CALL: model=gpt-4o operation=chat_completion
```

### Chat Request (INFO level)
```
[14:23:14.998] INFO  💬 CHAT_REQUEST: session_id=session-123 message_length=45 has_cosmosdb=true
```

### Span Events (DEBUG level)
```
[14:23:15.000] DEBUG 🔵 SPAN_START: span=agent.invoke module=ai.agent
[14:23:15.234] DEBUG 🟢 SPAN_END: span=agent.invoke duration_ms=234.5 status=OK
```

### Error Events (ERROR level)
```
[14:23:16.001] ERROR ❌ ERROR: operation=cosmosdb_save error=ConnectionTimeout
```

## Integration Points

The console output is automatically integrated into:

1. **Token Tracking** - All OpenAI API calls with token usage
2. **Span Events** - Function entry/exit when using decorators
3. **Telemetry Events** - Custom application events
4. **Configuration** - Telemetry setup and initialization
5. **Error Handling** - Automatic error reporting

## Code Usage Examples

### Automatic (via decorators)
```python
from telemetry.decorators import trace_async_method

@trace_async_method()  # Automatically logs span start/end
async def my_function():
    # Your code here
    pass
```

### Manual Telemetry Events
```python
from telemetry.console_output import console_telemetry_event

console_telemetry_event("database_save", {
    "collection": "chat_history",
    "document_id": "123",
    "operation_time_ms": 45.2
})
```

### Direct Console Output
```python
from telemetry.console_output import console_info, console_error

console_info("Processing user request")
console_error("Failed to connect to database")
```

## Best Practices

1. **Production Environments**: Use `WARNING` or `ERROR` level to reduce noise
2. **Development**: Use `DEBUG` or `INFO` level for detailed insights
3. **CI/CD**: Disable colors (`TELEMETRY_CONSOLE_COLORS=false`) for log aggregation
4. **Container Deployments**: Keep timestamps enabled for log correlation
5. **Local Development**: Enable modules for easier debugging

## Performance Impact

The console output system is designed for minimal performance impact:

- **Disabled**: Zero overhead when `TELEMETRY_CONSOLE_ENABLED=false`
- **Level Filtering**: Early return for messages below threshold
- **Lazy Formatting**: Messages only formatted if they will be displayed
- **Async Safe**: Thread-safe for concurrent operations
