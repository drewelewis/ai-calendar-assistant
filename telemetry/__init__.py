# OpenTelemetry telemetry package

from .config import (
    TelemetryConfig,
    initialize_telemetry,
    get_telemetry,
    get_tracer,
    get_meter,
    get_logger
)

from .decorators import (
    trace_async_method,
    trace_method,
    measure_performance,
    TelemetryContext,
    add_span_attributes,
    record_metric,
    log_with_trace
)

# Note: console_output imports removed to prevent circular dependencies
# Import console functions directly where needed:
# from telemetry.console_output import console_info, console_error, etc.

from .token_tracking import (
    track_openai_tokens,
    add_token_span_attributes,
    record_token_metrics,
    extract_token_usage,
    calculate_token_cost
)

from .semantic_kernel_instrumentation import (
    instrument_semantic_kernel,
    uninstrument_semantic_kernel,
    is_semantic_kernel_instrumented
)

__all__ = [
    'TelemetryConfig',
    'initialize_telemetry',
    'get_telemetry',
    'get_tracer',
    'get_meter',
    'get_logger',
    'trace_async_method',
    'trace_method',
    'measure_performance',
    'TelemetryContext',
    'add_span_attributes',
    'record_metric',
    'log_with_trace'
]
