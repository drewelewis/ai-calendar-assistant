"""
Token tracking utilities for OpenAI API calls
Provides per-request spans and aggregated metrics for token usage and cost monitoring
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, Union
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .config import get_tracer, get_meter, get_logger


# Token pricing in USD per 1K tokens (approximate values for GPT-4o)
# These should be updated based on current Azure OpenAI pricing
TOKEN_PRICING = {
    "gpt-4o": {
        "input": 0.005,   # $0.005 per 1K input tokens
        "output": 0.015,  # $0.015 per 1K output tokens
    },
    "gpt-4o-mini": {
        "input": 0.00015,  # $0.00015 per 1K input tokens
        "output": 0.0006,  # $0.0006 per 1K output tokens
    },
    "gpt-4": {
        "input": 0.03,    # $0.03 per 1K input tokens
        "output": 0.06,   # $0.06 per 1K output tokens
    },
    "gpt-35-turbo": {
        "input": 0.0015,  # $0.0015 per 1K input tokens
        "output": 0.002,  # $0.002 per 1K output tokens
    }
}


def calculate_token_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the estimated cost of token usage.
    
    Args:
        model: The model name/deployment
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    # Find matching pricing model (handle deployment names that might contain model names)
    pricing = None
    for model_key in TOKEN_PRICING:
        if model_key.lower() in model.lower():
            pricing = TOKEN_PRICING[model_key]
            break
    
    if not pricing:
        # Default to gpt-4o pricing if model not found
        pricing = TOKEN_PRICING["gpt-4o"]
    
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    
    return input_cost + output_cost


def extract_token_usage(response) -> Dict[str, int]:
    """
    Extract token usage information from OpenAI response.
    
    Args:
        response: OpenAI API response object
        
    Returns:
        Dictionary with token usage information
    """
    token_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
    
    try:
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            token_usage["prompt_tokens"] = getattr(usage, 'prompt_tokens', 0)
            token_usage["completion_tokens"] = getattr(usage, 'completion_tokens', 0)
            token_usage["total_tokens"] = getattr(usage, 'total_tokens', 0)
        elif hasattr(response, 'token_usage') and response.token_usage:
            # Alternative attribute name
            usage = response.token_usage
            token_usage["prompt_tokens"] = getattr(usage, 'prompt_tokens', 0)
            token_usage["completion_tokens"] = getattr(usage, 'completion_tokens', 0)
            token_usage["total_tokens"] = getattr(usage, 'total_tokens', 0)
    except Exception as e:
        logger = get_logger()
        if logger:
            logger.warning(f"Failed to extract token usage: {e}")
    
    return token_usage


def track_openai_tokens(model_name: str = None, operation_name: str = None):
    """
    Decorator to track token usage for OpenAI API calls.
    
    Adds token information to spans and records aggregated metrics.
    
    Args:
        model_name: The model/deployment name (will attempt to extract if not provided)
        operation_name: Custom operation name for the span
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            meter = get_meter()
            logger = get_logger()
            
            span_name = operation_name or f"openai.{func.__name__}"
            start_time = time.time()
            
            with tracer.start_as_current_span(span_name) as span:
                # Add basic span attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("openai.operation", func.__name__)
                
                # Add model name if provided
                if model_name:
                    span.set_attribute("openai.model", model_name)
                
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Extract token usage from response
                    token_usage = extract_token_usage(result)
                    
                    # Determine model name if not provided
                    effective_model = model_name
                    if not effective_model:
                        # Try to extract from args/kwargs or use default
                        if hasattr(result, 'model'):
                            effective_model = result.model
                        else:
                            effective_model = "unknown"
                    
                    # Add token information to span
                    span.set_attribute("openai.tokens.prompt", token_usage["prompt_tokens"])
                    span.set_attribute("openai.tokens.completion", token_usage["completion_tokens"])
                    span.set_attribute("openai.tokens.total", token_usage["total_tokens"])
                    span.set_attribute("openai.model", effective_model)
                    span.set_attribute("openai.duration_ms", duration_ms)
                    
                    # Calculate estimated cost
                    estimated_cost = calculate_token_cost(
                        effective_model,
                        token_usage["prompt_tokens"],
                        token_usage["completion_tokens"]
                    )
                    span.set_attribute("openai.cost.estimated_usd", estimated_cost)
                    span.set_attribute("openai.cost.estimated_cents", estimated_cost * 100)
                    
                    # Record aggregated metrics
                    if meter:
                        attributes = {
                            "model": effective_model,
                            "operation": func.__name__,
                            "status": "success"
                        }
                        
                        # Token usage metrics
                        meter.create_counter("openai_tokens_total", "Total tokens used", "tokens").add(
                            token_usage["total_tokens"], 
                            {**attributes, "token_type": "total"}
                        )
                        meter.create_counter("openai_tokens_total", "Total tokens used", "tokens").add(
                            token_usage["prompt_tokens"],
                            {**attributes, "token_type": "prompt"}
                        )
                        meter.create_counter("openai_tokens_total", "Total tokens used", "tokens").add(
                            token_usage["completion_tokens"],
                            {**attributes, "token_type": "completion"}
                        )
                        
                        # Cost metrics (in cents for better precision)
                        meter.create_counter("openai_token_cost_total", "Total estimated cost", "usd_cents").add(
                            estimated_cost * 100, attributes
                        )
                        
                        # Duration metrics
                        meter.create_histogram("openai_request_duration_ms", "Request duration", "ms").record(
                            duration_ms, attributes
                        )
                    
                    # Log token usage
                    if logger:
                        logger.info(
                            f"OpenAI API call completed - Model: {effective_model}, "
                            f"Tokens: {token_usage['total_tokens']} "
                            f"(prompt: {token_usage['prompt_tokens']}, "
                            f"completion: {token_usage['completion_tokens']}), "
                            f"Cost: ${estimated_cost:.4f}, "
                            f"Duration: {duration_ms:.2f}ms"
                        )
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record error metrics
                    if meter:
                        attributes = {
                            "model": model_name or "unknown",
                            "operation": func.__name__,
                            "status": "error"
                        }
                        meter.create_histogram("openai_request_duration_ms", "Request duration", "ms").record(
                            duration_ms, attributes
                        )
                    
                    # Add error information to span
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("openai.duration_ms", duration_ms)
                    
                    if logger:
                        logger.error(f"OpenAI API call failed after {duration_ms:.2f}ms: {e}")
                    
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            meter = get_meter()
            logger = get_logger()
            
            span_name = operation_name or f"openai.{func.__name__}"
            start_time = time.time()
            
            with tracer.start_as_current_span(span_name) as span:
                # Add basic span attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("openai.operation", func.__name__)
                
                # Add model name if provided
                if model_name:
                    span.set_attribute("openai.model", model_name)
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Extract token usage from response
                    token_usage = extract_token_usage(result)
                    
                    # Determine model name if not provided
                    effective_model = model_name
                    if not effective_model:
                        # Try to extract from args/kwargs or use default
                        if hasattr(result, 'model'):
                            effective_model = result.model
                        else:
                            effective_model = "unknown"
                    
                    # Add token information to span
                    span.set_attribute("openai.tokens.prompt", token_usage["prompt_tokens"])
                    span.set_attribute("openai.tokens.completion", token_usage["completion_tokens"])
                    span.set_attribute("openai.tokens.total", token_usage["total_tokens"])
                    span.set_attribute("openai.model", effective_model)
                    span.set_attribute("openai.duration_ms", duration_ms)
                    
                    # Calculate estimated cost
                    estimated_cost = calculate_token_cost(
                        effective_model,
                        token_usage["prompt_tokens"],
                        token_usage["completion_tokens"]
                    )
                    span.set_attribute("openai.cost.estimated_usd", estimated_cost)
                    span.set_attribute("openai.cost.estimated_cents", estimated_cost * 100)
                    
                    # Record aggregated metrics
                    if meter:
                        attributes = {
                            "model": effective_model,
                            "operation": func.__name__,
                            "status": "success"
                        }
                        
                        # Token usage metrics
                        meter.create_counter("openai_tokens_total", "Total tokens used", "tokens").add(
                            token_usage["total_tokens"], 
                            {**attributes, "token_type": "total"}
                        )
                        meter.create_counter("openai_tokens_total", "Total tokens used", "tokens").add(
                            token_usage["prompt_tokens"],
                            {**attributes, "token_type": "prompt"}
                        )
                        meter.create_counter("openai_tokens_total", "Total tokens used", "tokens").add(
                            token_usage["completion_tokens"],
                            {**attributes, "token_type": "completion"}
                        )
                        
                        # Cost metrics (in cents for better precision)
                        meter.create_counter("openai_token_cost_total", "Total estimated cost", "usd_cents").add(
                            estimated_cost * 100, attributes
                        )
                        
                        # Duration metrics
                        meter.create_histogram("openai_request_duration_ms", "Request duration", "ms").record(
                            duration_ms, attributes
                        )
                    
                    # Log token usage
                    if logger:
                        logger.info(
                            f"OpenAI API call completed - Model: {effective_model}, "
                            f"Tokens: {token_usage['total_tokens']} "
                            f"(prompt: {token_usage['prompt_tokens']}, "
                            f"completion: {token_usage['completion_tokens']}), "
                            f"Cost: ${estimated_cost:.4f}, "
                            f"Duration: {duration_ms:.2f}ms"
                        )
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record error metrics
                    if meter:
                        attributes = {
                            "model": model_name or "unknown",
                            "operation": func.__name__,
                            "status": "error"
                        }
                        meter.create_histogram("openai_request_duration_ms", "Request duration", "ms").record(
                            duration_ms, attributes
                        )
                    
                    # Add error information to span
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("openai.duration_ms", duration_ms)
                    
                    if logger:
                        logger.error(f"OpenAI API call failed after {duration_ms:.2f}ms: {e}")
                    
                    raise
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def add_token_span_attributes(response, model_name: str = None):
    """
    Add token usage attributes to the current span.
    
    Args:
        response: OpenAI API response
        model_name: Optional model name
    """
    current_span = trace.get_current_span()
    if not current_span or not current_span.is_recording():
        return
    
    token_usage = extract_token_usage(response)
    
    # Add token attributes
    current_span.set_attribute("openai.tokens.prompt", token_usage["prompt_tokens"])
    current_span.set_attribute("openai.tokens.completion", token_usage["completion_tokens"])
    current_span.set_attribute("openai.tokens.total", token_usage["total_tokens"])
    
    if model_name:
        current_span.set_attribute("openai.model", model_name)
        
        # Calculate and add cost information
        estimated_cost = calculate_token_cost(
            model_name,
            token_usage["prompt_tokens"],
            token_usage["completion_tokens"]
        )
        current_span.set_attribute("openai.cost.estimated_usd", estimated_cost)
        current_span.set_attribute("openai.cost.estimated_cents", estimated_cost * 100)


def record_token_metrics(response, model_name: str, operation: str = "unknown"):
    """
    Record token usage metrics from an OpenAI response.
    
    Args:
        response: OpenAI API response
        model_name: Model name
        operation: Operation name for metric labeling
    """
    meter = get_meter()
    if not meter:
        return
    
    token_usage = extract_token_usage(response)
    estimated_cost = calculate_token_cost(
        model_name,
        token_usage["prompt_tokens"],
        token_usage["completion_tokens"]
    )
    
    attributes = {
        "model": model_name,
        "operation": operation,
        "status": "success"
    }
    
    # Record token metrics
    token_counter = meter.create_counter("openai_tokens_total", "Total tokens used", "tokens")
    token_counter.add(token_usage["total_tokens"], {**attributes, "token_type": "total"})
    token_counter.add(token_usage["prompt_tokens"], {**attributes, "token_type": "prompt"})
    token_counter.add(token_usage["completion_tokens"], {**attributes, "token_type": "completion"})
    
    # Record cost metrics
    cost_counter = meter.create_counter("openai_token_cost_total", "Total estimated cost", "usd_cents")
    cost_counter.add(estimated_cost * 100, attributes)
