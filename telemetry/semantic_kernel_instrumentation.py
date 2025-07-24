"""
Semantic Kernel OpenAI instrumentation for token tracking
Provides automatic token tracking for Semantic Kernel's Azure OpenAI service calls
"""

import functools
import time
from typing import Any, Dict, Optional
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .token_tracking import extract_token_usage, calculate_token_cost, add_token_span_attributes, record_token_metrics
from .config import get_tracer, get_meter, get_logger


def _extract_token_usage(usage) -> Dict[str, int]:
    """
    Safely extract token usage from either dictionary or object format.
    Handles both CompletionUsage objects and dictionary formats gracefully.
    """
    try:
        # Initialize default values
        default_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        if usage is None:
            return default_usage
        
        # Handle dictionary format
        if isinstance(usage, dict):
            return {
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0),
                "total_tokens": usage.get('total_tokens', 0)
            }
        
        # Handle object format (like CompletionUsage)
        return {
            "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
            "completion_tokens": getattr(usage, 'completion_tokens', 0),
            "total_tokens": getattr(usage, 'total_tokens', 0)
        }
        
    except Exception as e:
        # Log the error but don't let telemetry break the application
        logger = get_logger()
        if logger:
            logger.warning(f"Failed to extract token usage safely: {e}")
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


class SemanticKernelInstrumentation:
    """
    Instrumentation for Semantic Kernel OpenAI service calls.
    Automatically tracks token usage and costs for all SK OpenAI operations.
    """
    
    def __init__(self):
        self.is_instrumented = False
        self._original_methods = {}
    
    def instrument(self):
        """Instrument Semantic Kernel's Azure OpenAI service."""
        if self.is_instrumented:
            return
        
        try:
            # Import SK modules
            from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
            
            # Patch the chat completion method
            if hasattr(AzureChatCompletion, '_inner_get_chat_message_contents'):
                self._patch_method(
                    AzureChatCompletion,
                    '_inner_get_chat_message_contents',
                    self._trace_chat_completion
                )
            elif hasattr(AzureChatCompletion, 'get_chat_message_contents'):
                self._patch_method(
                    AzureChatCompletion,
                    'get_chat_message_contents',
                    self._trace_chat_completion
                )
            
            self.is_instrumented = True
            logger = get_logger()
            if logger:
                logger.info("✅ Semantic Kernel OpenAI instrumentation enabled")
                
        except ImportError as e:
            logger = get_logger()
            if logger:
                logger.warning(f"Could not instrument Semantic Kernel: {e}")
        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"Failed to instrument Semantic Kernel: {e}")
    
    def uninstrument(self):
        """Remove instrumentation from Semantic Kernel."""
        if not self.is_instrumented:
            return
        
        # Restore original methods
        for (cls, method_name), original_method in self._original_methods.items():
            setattr(cls, method_name, original_method)
        
        self._original_methods.clear()
        self.is_instrumented = False
        
        logger = get_logger()
        if logger:
            logger.info("Semantic Kernel OpenAI instrumentation removed")
    
    def _patch_method(self, cls, method_name: str, wrapper_factory):
        """Patch a method with instrumentation."""
        original_method = getattr(cls, method_name)
        self._original_methods[(cls, method_name)] = original_method
        
        # Create the wrapped method
        wrapped_method = wrapper_factory(original_method)
        setattr(cls, method_name, wrapped_method)
    
    def _trace_chat_completion(self, original_method):
        """Create a traced version of the chat completion method."""
        @functools.wraps(original_method)
        async def wrapper(self, *args, **kwargs):
            tracer = get_tracer()
            meter = get_meter()
            logger = get_logger()
            
            # Extract model information
            model_name = getattr(self, 'deployment_name', None) or getattr(self, 'model_id', 'unknown')
            
            span_name = f"semantic_kernel.azure_openai.chat_completion"
            start_time = time.time()
            
            with tracer.start_as_current_span(span_name) as span:
                # Add span attributes
                span.set_attribute("sk.service.type", "azure_openai")
                span.set_attribute("sk.operation", "chat_completion")
                span.set_attribute("openai.model", model_name)
                span.set_attribute("sk.deployment_name", model_name)
                
                # Add input information if available
                if args and len(args) > 0:
                    # First arg is usually chat_history or messages
                    chat_history = args[0]
                    if hasattr(chat_history, '__len__'):
                        span.set_attribute("sk.chat_history.length", len(chat_history))
                
                # Extract settings information
                if kwargs.get('settings'):
                    settings = kwargs['settings']
                    # Handle both max_tokens (older API) and max_completion_tokens (newer API)
                    if hasattr(settings, 'max_completion_tokens'):
                        span.set_attribute("openai.request.max_completion_tokens", settings.max_completion_tokens)
                    elif hasattr(settings, 'max_tokens'):
                        span.set_attribute("openai.request.max_tokens", settings.max_tokens)
                    if hasattr(settings, 'temperature'):
                        span.set_attribute("openai.request.temperature", settings.temperature)
                
                try:
                    # Call the original method
                    result = await original_method(self, *args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Try to extract token usage from the result - wrap in try-catch for graceful failure
                    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    
                    try:
                        # SK usually returns a list of ChatMessageContent objects
                        if isinstance(result, list) and len(result) > 0:
                            first_result = result[0]
                            
                            # Check for metadata containing usage information
                            if hasattr(first_result, 'metadata') and first_result.metadata:
                                metadata = first_result.metadata
                                
                                # Look for usage information in metadata
                                if 'usage' in metadata:
                                    usage = metadata['usage']
                                    token_usage = _extract_token_usage(usage)
                                elif 'token_usage' in metadata:
                                    usage = metadata['token_usage']
                                    token_usage = _extract_token_usage(usage)
                            
                            # Also check if the result has usage information directly
                            if hasattr(first_result, 'usage') and first_result.usage:
                                usage = first_result.usage
                                token_usage = _extract_token_usage(usage)
                        
                        # Add token information to span
                        span.set_attribute("openai.tokens.prompt", token_usage["prompt_tokens"])
                        span.set_attribute("openai.tokens.completion", token_usage["completion_tokens"])
                        span.set_attribute("openai.tokens.total", token_usage["total_tokens"])
                        span.set_attribute("openai.duration_ms", duration_ms)
                        
                        # Calculate estimated cost
                        estimated_cost = calculate_token_cost(
                            model_name,
                            token_usage["prompt_tokens"],
                            token_usage["completion_tokens"]
                        )
                        span.set_attribute("openai.cost.estimated_usd", estimated_cost)
                        span.set_attribute("openai.cost.estimated_cents", estimated_cost * 100)
                        
                    except Exception as telemetry_error:
                        # Log telemetry extraction error but don't fail the operation
                        if logger:
                            logger.warning(f"Failed to extract telemetry data (operation continues): {telemetry_error}")
                        # Set minimal telemetry to show operation completed
                        span.set_attribute("openai.duration_ms", duration_ms)
                        span.set_attribute("telemetry.extraction_failed", True)
                    
                    # Record aggregated metrics - also wrap in try-catch
                    try:
                        if meter:
                            attributes = {
                                "model": model_name,
                                "operation": "chat_completion",
                                "service": "semantic_kernel",
                                "status": "success"
                            }
                            
                            # Token usage metrics
                            token_counter = meter.create_counter("openai_tokens_total", "Total tokens used", "tokens")
                            token_counter.add(token_usage["total_tokens"], {**attributes, "token_type": "total"})
                            token_counter.add(token_usage["prompt_tokens"], {**attributes, "token_type": "prompt"})
                            token_counter.add(token_usage["completion_tokens"], {**attributes, "token_type": "completion"})
                            
                            # Cost metrics (in cents for better precision)
                            cost_counter = meter.create_counter("openai_token_cost_total", "Total estimated cost", "usd_cents")
                            estimated_cost = calculate_token_cost(
                                model_name,
                                token_usage["prompt_tokens"],
                                token_usage["completion_tokens"]
                            )
                            cost_counter.add(estimated_cost * 100, attributes)
                            
                            # Duration metrics
                            duration_histogram = meter.create_histogram("openai_request_duration_ms", "Request duration", "ms")
                            duration_histogram.record(duration_ms, attributes)
                        
                        # Log token usage
                        if logger and token_usage["total_tokens"] > 0:
                            estimated_cost = calculate_token_cost(
                                model_name,
                                token_usage["prompt_tokens"],
                                token_usage["completion_tokens"]
                            )
                            logger.info(
                                f"SK OpenAI API call completed - Model: {model_name}, "
                                f"Tokens: {token_usage['total_tokens']} "
                                f"(prompt: {token_usage['prompt_tokens']}, "
                                f"completion: {token_usage['completion_tokens']}), "
                                f"Cost: ${estimated_cost:.4f}, "
                                f"Duration: {duration_ms:.2f}ms"
                            )
                    except Exception as metrics_error:
                        # Log metrics error but don't fail the operation
                        if logger:
                            logger.warning(f"Failed to record metrics (operation continues): {metrics_error}")
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record error metrics - wrap in try-catch
                    try:
                        if meter:
                            attributes = {
                                "model": model_name,
                                "operation": "chat_completion",
                                "service": "semantic_kernel",
                                "status": "error"
                            }
                            duration_histogram = meter.create_histogram("openai_request_duration_ms", "Request duration", "ms")
                            duration_histogram.record(duration_ms, attributes)
                    except Exception as metrics_error:
                        # Log metrics error but don't fail the operation
                        if logger:
                            logger.warning(f"Failed to record error metrics: {metrics_error}")
                    
                    # Add error information to span - wrap in try-catch
                    try:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.set_attribute("openai.duration_ms", duration_ms)
                    except Exception as span_error:
                        # Log span error but don't fail the operation
                        if logger:
                            logger.warning(f"Failed to set span attributes: {span_error}")
                    
                    if logger:
                        logger.error(f"SK OpenAI API call failed after {duration_ms:.2f}ms: {e}")
                    
                    raise
        
        return wrapper


# Global instrumentation instance
_sk_instrumentation: Optional[SemanticKernelInstrumentation] = None


def instrument_semantic_kernel():
    """Enable automatic token tracking for Semantic Kernel OpenAI calls."""
    global _sk_instrumentation
    
    if _sk_instrumentation is None:
        _sk_instrumentation = SemanticKernelInstrumentation()
    
    _sk_instrumentation.instrument()


def uninstrument_semantic_kernel():
    """Disable automatic token tracking for Semantic Kernel OpenAI calls."""
    global _sk_instrumentation
    
    if _sk_instrumentation:
        _sk_instrumentation.uninstrument()


def is_semantic_kernel_instrumented() -> bool:
    """Check if Semantic Kernel is currently instrumented."""
    global _sk_instrumentation
    return _sk_instrumentation is not None and _sk_instrumentation.is_instrumented
