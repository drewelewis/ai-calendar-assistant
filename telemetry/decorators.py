"""
Telemetry decorators and utilities for easy instrumentation
"""

import functools
import time
from typing import Any, Callable, Optional, Dict
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .config import get_tracer, get_meter, get_logger


def trace_async_method(operation_name: Optional[str] = None, 
                      include_args: bool = False,
                      include_result: bool = False):
    """
    Decorator to trace async methods with OpenTelemetry.
    
    Args:
        operation_name: Custom name for the operation (defaults to function name)
        include_args: Whether to include function arguments in span attributes
        include_result: Whether to include return value in span attributes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            if not tracer:
                return await func(*args, **kwargs)
            
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            with tracer.start_as_current_span(span_name) as span:
                # Console output for span start
                span_attrs = {"module": func.__module__}
                if include_args and args:
                    span_attrs["args_count"] = len(args)
                if include_args and kwargs:
                    span_attrs["kwargs_count"] = len(kwargs)
                # Span start logged
                
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add arguments if requested
                if include_args and args:
                    for i, arg in enumerate(args):
                        if i == 0 and hasattr(arg, '__class__'):
                            # Skip 'self' parameter for methods
                            span.set_attribute("method.class", arg.__class__.__name__)
                        else:
                            span.set_attribute(f"args.{i}", str(arg)[:100])  # Truncate long values
                
                if include_args and kwargs:
                    for key, value in kwargs.items():
                        span.set_attribute(f"kwargs.{key}", str(value)[:100])
                
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Add result if requested
                    if include_result and result is not None:
                        span.set_attribute("result.type", type(result).__name__)
                        if isinstance(result, (str, int, float, bool)):
                            span.set_attribute("result.value", str(result)[:100])
                    
                    span.set_status(Status(StatusCode.OK))
                    
                    # Console output for span end
                    # Span end logged
                    return result
                
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    
                    # Console output for span end with error
                    # Span end logged.__name__})
                    raise
        
        return wrapper
    return decorator


def trace_method(operation_name: Optional[str] = None,
                include_args: bool = False,
                include_result: bool = False):
    """
    Decorator to trace sync methods with OpenTelemetry.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            if not tracer:
                return func(*args, **kwargs)
            
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add arguments if requested
                if include_args and args:
                    for i, arg in enumerate(args):
                        if i == 0 and hasattr(arg, '__class__'):
                            # Skip 'self' parameter for methods
                            span.set_attribute("method.class", arg.__class__.__name__)
                        else:
                            span.set_attribute(f"args.{i}", str(arg)[:100])
                
                if include_args and kwargs:
                    for key, value in kwargs.items():
                        span.set_attribute(f"kwargs.{key}", str(value)[:100])
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Add result if requested
                    if include_result and result is not None:
                        span.set_attribute("result.type", type(result).__name__)
                        if isinstance(result, (str, int, float, bool)):
                            span.set_attribute("result.value", str(result)[:100])
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        
        return wrapper
    return decorator


def measure_performance(metric_name: str, 
                       additional_attributes: Optional[Dict[str, str]] = None):
    """
    Decorator to measure method performance and record metrics.
    
    Args:
        metric_name: Name of the metric to record
        additional_attributes: Additional attributes to include with the metric
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            meter = get_meter()
            logger = get_logger()
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if meter:
                    # Record duration histogram
                    histogram = meter.create_histogram(
                        name=f"{metric_name}_duration_ms",
                        description=f"Duration of {func.__name__} operations",
                        unit="ms"
                    )
                    
                    attributes = {"operation": func.__name__, "status": "success"}
                    if additional_attributes:
                        attributes.update(additional_attributes)
                    
                    histogram.record(duration_ms, attributes)
                
                if logger:
                    logger.info(f"{func.__name__} completed in {duration_ms:.2f}ms")
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if meter:
                    histogram = meter.create_histogram(
                        name=f"{metric_name}_duration_ms",
                        description=f"Duration of {func.__name__} operations",
                        unit="ms"
                    )
                    
                    attributes = {"operation": func.__name__, "status": "error"}
                    if additional_attributes:
                        attributes.update(additional_attributes)
                    
                    histogram.record(duration_ms, attributes)
                
                if logger:
                    logger.error(f"{func.__name__} failed after {duration_ms:.2f}ms: {e}")
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            meter = get_meter()
            logger = get_logger()
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if meter:
                    histogram = meter.create_histogram(
                        name=f"{metric_name}_duration_ms",
                        description=f"Duration of {func.__name__} operations",
                        unit="ms"
                    )
                    
                    attributes = {"operation": func.__name__, "status": "success"}
                    if additional_attributes:
                        attributes.update(additional_attributes)
                    
                    histogram.record(duration_ms, attributes)
                
                if logger:
                    logger.info(f"{func.__name__} completed in {duration_ms:.2f}ms")
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if meter:
                    histogram = meter.create_histogram(
                        name=f"{metric_name}_duration_ms",
                        description=f"Duration of {func.__name__} operations",
                        unit="ms"
                    )
                    
                    attributes = {"operation": func.__name__, "status": "error"}
                    if additional_attributes:
                        attributes.update(additional_attributes)
                    
                    histogram.record(duration_ms, attributes)
                
                if logger:
                    logger.error(f"{func.__name__} failed after {duration_ms:.2f}ms: {e}")
                
                raise
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class TelemetryContext:
    """Context manager for adding custom telemetry attributes to current span."""
    
    def __init__(self, **attributes):
        self.attributes = attributes
        self.span = None
    
    def __enter__(self):
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            for key, value in self.attributes.items():
                current_span.set_attribute(key, str(value))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                current_span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                current_span.set_attribute("error.type", exc_type.__name__)
                current_span.set_attribute("error.message", str(exc_val))


def add_span_attributes(**attributes):
    """Add attributes to the current span."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))


def record_metric(name: str, value: float, attributes: Optional[Dict[str, str]] = None):
    """Record a custom metric value."""
    meter = get_meter()
    if meter:
        counter = meter.create_counter(
            name=name,
            description=f"Custom metric: {name}",
            unit="1"
        )
        counter.add(value, attributes or {})


def log_with_trace(level: str, message: str, **kwargs):
    """Log a message with trace correlation."""
    logger = get_logger()
    if logger:
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            trace_id = format(span_context.trace_id, '032x')
            span_id = format(span_context.span_id, '016x')
            extra = {'otelTraceID': trace_id, 'otelSpanID': span_id}
            extra.update(kwargs)
        else:
            extra = kwargs
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message, extra=extra)
