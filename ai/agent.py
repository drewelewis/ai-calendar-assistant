# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import uuid
import logging
from typing import Annotated
import datetime
import colorama
import time
import random
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager

from plugins.graph_plugin import GraphPlugin
from plugins.azure_maps_plugin import AzureMapsPlugin
from plugins.risk_plugin import RiskPlugin
from prompts.graph_prompts import prompts
from utils.teams_utilities import TeamsUtilities
from utils.thread_utilities import ThreadUtilities

# Initialize TeamsUtilities for sending messages
teams_utils = TeamsUtilities()

# Import telemetry components
from telemetry.config import initialize_telemetry, get_telemetry
from telemetry.decorators import trace_async_method, measure_performance, TelemetryContext
from telemetry.token_tracking import add_token_span_attributes, record_token_metrics
from telemetry.console_output import console_info, console_debug, console_telemetry_event
 
load_dotenv(override=True)

class Agent:
    def __init__(self, session_id: str = None):
        
        self.session_id = session_id
        
        # Initialize telemetry first
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant")
        service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")
        
        telemetry_success = initialize_telemetry(
            service_name=service_name,
            service_version=service_version
        )
        
        # Create custom metrics
        if telemetry_success:
            self.telemetry = get_telemetry()
            self.metrics = self.telemetry.create_custom_metrics() if self.telemetry else {}
            self.logger = self.telemetry.get_logger() if self.telemetry else logging.getLogger(__name__)
        else:
            self.telemetry = None
            self.metrics = {}
            import logging
            self.logger = logging.getLogger(__name__)
            import logging
            self.logger = logging.getLogger(__name__)
        
        # 1. Load environment variables
        self.endpoint = os.getenv("OPENAI_ENDPOINT")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_version = os.getenv("OPENAI_API_VERSION")
        self.deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_database = os.getenv("COSMOS_DATABASE", "AIAssistant")
        self.cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
        
        # Azure OpenAI retry configuration
        # Detect if using o1 model for optimized defaults
        is_o1_model = "o1" in os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME", "").lower()
        
        # Set retry defaults based on model type
        if is_o1_model:
            # o1 models need more time for reasoning, so use longer delays
            default_base_delay = "2.0"
            default_max_delay = "120.0"
            self.logger.info("Detected o1 model - using extended retry delays for reasoning time")
        else:
            default_base_delay = "1.0"
            default_max_delay = "60.0"
        
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        self.base_delay = float(os.getenv("OPENAI_BASE_DELAY", default_base_delay))
        self.max_delay = float(os.getenv("OPENAI_MAX_DELAY", default_max_delay))
        self.jitter = True  # Add randomization to prevent thundering herd
        
        # Log initialization
        self.logger.info(f"Initializing Agent with session_id: {session_id}")
        
        # Validate required OpenAI environment variables
        if not all([self.endpoint, self.api_key, self.deployment_name]):
            error_msg = ("Missing required OpenAI environment variables. Please ensure OPENAI_ENDPOINT, "
                        "OPENAI_API_KEY, and OPENAI_MODEL_DEPLOYMENT_NAME are set in the .env file.")
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Initialize CosmosDB if endpoint is configured
        if self.cosmos_endpoint:
            try:
                with TelemetryContext(operation="cosmosdb_init", cosmos_endpoint=self.cosmos_endpoint):
                    self.cosmos_manager = CosmosDBChatHistoryManager(
                        self.cosmos_endpoint, 
                        self.cosmos_database, 
                        self.cosmos_container
                    )
                    self.logger.info("✅ CosmosDB initialized successfully")
                    
                    # Record successful initialization - wrap in try-catch
                    try:
                        if 'cosmosdb_operations_total' in self.metrics:
                            self.metrics['cosmosdb_operations_total'].add(1, {"operation": "init", "status": "success"})
                    except Exception as e:
                        self.logger.warning(f"Failed to record CosmosDB init success metric: {e}")
                        
            except Exception as e:
                self.logger.error(f"⚠ Warning: Failed to initialize CosmosDB: {e}")
                
                # Record failed initialization - wrap in try-catch
                try:
                    if 'cosmosdb_operations_total' in self.metrics:
                        self.metrics['cosmosdb_operations_total'].add(1, {"operation": "init", "status": "error"})
                except Exception as metric_error:
                    self.logger.warning(f"Failed to record CosmosDB init error metric: {metric_error}")
                
                # Provide specific guidance based on error type
                if "ManagedIdentityCredential" in str(e) or "No managed identity endpoint found" in str(e):
                    print("🔐 MANAGED IDENTITY ISSUE DETECTED:")
                    print("   This appears to be a production managed identity configuration problem.")
                    print("   📖 See '_production_managed_identity_setup.md' for detailed setup instructions.")
                    print("")
                    print("   Quick fixes to try:")
                    print("   1. Ensure managed identity is enabled on your Azure resource")
                    print("   2. Grant 'Cosmos DB Built-in Data Contributor' role to the managed identity")
                    print("   3. Verify local authentication is disabled on CosmosDB")
                elif "Request url is invalid" in str(e):
                    print("🔗 CosmosDB URL issue - check your COSMOS_ENDPOINT format")
                elif "insufficient privileges" in str(e).lower():
                    print("🔒 Permissions issue - managed identity needs CosmosDB data access role")
                else:
                    print("💡 General troubleshooting:")
                    print("   1. Check your COSMOS_ENDPOINT in .env file")
                    print("   2. Verify Azure authentication (managed identity in production, CLI in dev)")
                    print("   3. Ensure CosmosDB permissions are correctly configured")
                
                print("📝 Chat history will not be persisted until this is resolved.")
                self.cosmos_manager = None
        else:
            self.logger.info("ℹ COSMOS_ENDPOINT not configured. Chat history will not be persisted.")
            self.cosmos_manager = None
        
        # Initialize Teams utilities for sending messages
        self.teams_utils = TeamsUtilities()
        
        # Initialize Thread utilities for ensuring system/instruction messages
        self.thread_utils = ThreadUtilities()
        
        # 2. Create the Kernel and register plugins
        self.service_id = "agent"
        self.kernel = Kernel()

        # 3. Add the Microsoft Graph plugin with optional debug mode
        self.graph_debug = os.getenv("GRAPH_DEBUG", "false").lower() == "true"
        self.kernel.add_plugin(GraphPlugin(debug=self.graph_debug, session_id=self.session_id), plugin_name="graph")
        
        # Add the Azure Maps plugin for location-based searches
        self.kernel.add_plugin(AzureMapsPlugin(debug=self.graph_debug, session_id=self.session_id), plugin_name="azure_maps")
        self.logger.info("✅ Azure Maps plugin added for location-based searches")
        
        # Add the Risk Management plugin for client risk analysis
        self.kernel.add_plugin(RiskPlugin(debug=self.graph_debug, session_id=self.session_id), plugin_name="risk")
        self.logger.info("✅ Risk Management plugin added for client risk analysis")
        # self.kernel.add_plugin(OpenTablePlugin(), plugin_name="open_table")
       
        # 4. Add Azure OpenAI service to the kernel
        with TelemetryContext(operation="openai_service_init", endpoint=self.endpoint):
            self.kernel.add_service(AzureChatCompletion(
                deployment_name=self.deployment_name,
                endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version or "2023-05-15",
                service_id=self.service_id))
            
            self.logger.info(f"✅ Azure OpenAI service configured with deployment: {self.deployment_name}")
        
        # Configure execution settings with error prevention parameters
        self.settings = self.kernel.get_prompt_execution_settings_from_service_id(service_id=self.service_id)
        self.settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        
        # Add parameters to help prevent "invalid content" errors
        # These can be overridden by environment variables
        # Note: o1 models have different parameter support than GPT-4 models
        try:
            # Set max_completion_tokens to prevent excessively long responses that might be malformed
            # o1 models support higher token limits and longer reasoning chains
            # Note: Newer API versions use max_completion_tokens instead of max_tokens
            max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "8000"))  # Higher default for o1
            if hasattr(self.settings, 'max_completion_tokens'):
                self.settings.max_completion_tokens = max_tokens
                self.logger.debug(f"Set max_completion_tokens to {max_tokens}")
            elif hasattr(self.settings, 'max_tokens'):
                # Fallback for older API versions that still use max_tokens
                self.settings.max_tokens = max_tokens
                self.logger.debug(f"Set max_tokens to {max_tokens} (fallback)")
            
            # Check if this is an o1 model to avoid setting unsupported parameters
            is_o1_model = "o1" in self.deployment_name.lower() if self.deployment_name else False
            
            if not is_o1_model:
                # These parameters are only supported by non-o1 models
                # Set temperature for more deterministic responses (helps prevent hallucinations)
                temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
                if hasattr(self.settings, 'temperature'):
                    self.settings.temperature = temperature
                    self.logger.debug(f"Set temperature to {temperature}")
                
                # Set top_p for nucleus sampling (another parameter to control randomness)
                top_p = float(os.getenv("OPENAI_TOP_P", "0.9"))
                if hasattr(self.settings, 'top_p'):
                    self.settings.top_p = top_p
                    self.logger.debug(f"Set top_p to {top_p}")
            else:
                self.logger.info(f"Detected o1 model '{self.deployment_name}' - skipping temperature and top_p settings (not supported)")
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error setting OpenAI parameters, using defaults: {e}")

        # Create agent with properly structured instructions
        combined_instructions = prompts.build_complete_instructions(self.session_id)

        self.agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Agent",
            instructions=combined_instructions,
            arguments=KernelArguments(settings=self.settings),
        )
        
        # Log o1-specific initialization details
        if is_o1_model:
            self.logger.info("🧠 o1 Model Configuration Applied:")
            self.logger.info(f"   - Extended max_tokens: {max_tokens}")
            self.logger.info(f"   - Extended retry delays: base={self.base_delay}s, max={self.max_delay}s")
            self.logger.info(f"   - Extended response length limit: {os.getenv('MAX_RESPONSE_LENGTH', '100000')}")
            self.logger.info("   - Temperature and top_p parameters disabled (not supported by o1)")
        
        self.logger.info("✅ AI Calendar Assistant Agent initialized successfully")

    async def _retry_with_exponential_backoff(self, func, *args, **kwargs):
        """
        Retry function with exponential backoff for handling transient Azure OpenAI errors.
        
        Args:
            func: The async function to retry
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the successful function call
            
        Raises:
            The last exception if all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 because we want max_retries actual retries after first attempt
            try:
                # Try the function call
                result = await func(*args, **kwargs)
                
                # If we get here, the call was successful
                if attempt > 0:
                    self.logger.info(f"Azure OpenAI call succeeded on attempt {attempt + 1}")
                    
                    # Record successful retry - wrap in try-catch
                    try:
                        if 'openai_retries_total' in self.metrics:
                            self.metrics['openai_retries_total'].add(1, {
                                "model": self.deployment_name,
                                "attempt": str(attempt + 1),
                                "status": "success"
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to record retry success metric: {e}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if this is a retryable error
                # o1 models may have longer processing times, so include timeout-related errors
                is_retryable = (
                    "500" in error_str or 
                    "internal server error" in error_str or
                    "internalservererror" in error_str or
                    "invalid content" in error_str or
                    "timeout" in error_str or
                    "rate limit" in error_str or
                    "429" in error_str or
                    "502" in error_str or
                    "503" in error_str or
                    "504" in error_str or
                    "gateway timeout" in error_str or  # Common with o1 due to processing time
                    "processing timeout" in error_str  # o1-specific processing timeouts
                )
                
                if not is_retryable or attempt >= self.max_retries:
                    # Either not retryable or we've exhausted retries
                    self.logger.error(f"Azure OpenAI call failed permanently after {attempt + 1} attempts: {e}")
                    
                    # Record failed retry - wrap in try-catch
                    try:
                        if 'openai_retries_total' in self.metrics:
                            self.metrics['openai_retries_total'].add(1, {
                                "model": self.deployment_name,
                                "attempt": str(attempt + 1),
                                "status": "failed",
                                "error_type": type(e).__name__
                            })
                    except Exception as metric_e:
                        self.logger.warning(f"Failed to record retry failure metric: {metric_e}")
                    
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                if self.jitter:
                    delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                
                self.logger.warning(
                    f"Azure OpenAI call failed on attempt {attempt + 1}/{self.max_retries + 1}: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                # Record retry attempt - wrap in try-catch
                try:
                    if 'openai_retries_total' in self.metrics:
                        self.metrics['openai_retries_total'].add(1, {
                            "model": self.deployment_name,
                            "attempt": str(attempt + 1),
                            "status": "retry",
                            "error_type": type(e).__name__
                        })
                except Exception as metric_e:
                    self.logger.warning(f"Failed to record retry attempt metric: {metric_e}")
                
                await asyncio.sleep(delay)
        
        # This should never be reached due to the logic above, but just in case
        raise last_exception

    def _validate_response_content(self, response_content: str) -> bool:
        """
        Validate that the response content is well-formed and doesn't contain invalid characters.
        
        Args:
            response_content: The content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        try:
            # Check for basic validity
            if not response_content or not isinstance(response_content, str):
                self.logger.warning("Response content is empty or not a string")
                return False
            
            # Check for extremely long responses that might be malformed
            # o1 models can produce longer, more detailed responses, so use higher default
            is_o1_model = "o1" in self.deployment_name.lower() if self.deployment_name else False
            default_max_length = "100000" if is_o1_model else "50000"
            max_response_length = int(os.getenv("MAX_RESPONSE_LENGTH", default_max_length))
            
            if len(response_content) > max_response_length:
                self.logger.warning(f"Response content exceeds maximum length: {len(response_content)} > {max_response_length}")
                return False
            
            # Check for common invalid content patterns
            invalid_patterns = [
                "\x00",  # Null bytes
                "\uFFFD",  # Unicode replacement character (often indicates encoding issues)
            ]
            
            for pattern in invalid_patterns:
                if pattern in response_content:
                    self.logger.warning(f"Response contains invalid pattern: {pattern}")
                    return False
            
            # If content starts with { or [, try to validate as JSON
            stripped_content = response_content.strip()
            if stripped_content.startswith(("{", "[")):
                try:
                    json.loads(stripped_content)
                    self.logger.debug("Response content validated as valid JSON")
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Response appears to be JSON but is invalid: {e}")
                    # Don't return False here - might be partial JSON or JSON-like text
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating response content: {e}")
            return False


    @trace_async_method(operation_name="agent.invoke", include_args=True)
    @measure_performance("chat_request")
    async def invoke(self, message: str):
        
        # Record chat request metric - wrap in try-catch for graceful failure
        try:
            if 'chat_requests_total' in self.metrics:
                self.metrics['chat_requests_total'].add(1, {"session_id": self.session_id})
        except Exception as e:
            self.logger.warning(f"Failed to record chat request metric: {e}")
        
        # Log the incoming request
        self.logger.info(f"Processing chat request for session: {self.session_id}")
        
        # Console output for chat request - wrap in try-catch
        try:
            console_telemetry_event("chat_request", {
                "session_id": self.session_id,
                "message_length": len(message),
                "has_cosmosdb": self.cosmos_manager is not None
            }, "agent")
        except Exception as e:
            self.logger.warning(f"Failed to record console telemetry event: {e}")
        
        # Create or hydrate thread based on CosmosDB availability
        with TelemetryContext(operation="thread_creation", session_id=self.session_id):
            if self.cosmos_manager:
                thread = await self.cosmos_manager.create_hydrated_thread(self.kernel, self.session_id)
                self.logger.debug("Thread hydrated from CosmosDB")
            else:
                # Create a new empty thread if CosmosDB is not available
                from semantic_kernel.agents import ChatHistoryAgentThread
                thread = ChatHistoryAgentThread()
                self.logger.debug("Created new empty thread")
        
        # Process the request with the agent
        with TelemetryContext(operation="agent_response", message_length=len(message)):
            # Record OpenAI API call - wrap in try-catch for graceful failure
            try:
                if 'openai_api_calls_total' in self.metrics:
                    self.metrics['openai_api_calls_total'].add(1, {"model": self.deployment_name})
            except Exception as e:
                self.logger.warning(f"Failed to record OpenAI API call metric: {e}")
            
            
            # Ensure initial system + instruction messages are present on the thread
            try:
                thread = await self.thread_utils.ensure_system_and_instruction_messages(thread, self.session_id, prompts, self.logger)
            except Exception as e:
                self.logger.warning(f"Failed to ensure system/instruction messages on thread: {e}")

            # Track the OpenAI API call with token information
            with TelemetryContext(operation="openai_chat_completion", model=self.deployment_name):
                # Console output for OpenAI call start - wrap in try-catch
                try:
                    console_telemetry_event("openai_call", {
                        "model": self.deployment_name,
                        "operation": "chat_completion"
                    }, "agent")
                except Exception as e:
                    self.logger.warning(f"Failed to record console telemetry for OpenAI call: {e}")
                
                # Create a wrapper function for the OpenAI call that includes validation
                async def make_openai_call():
                    try:
                        # Make the actual OpenAI API call
                        response = await self.agent.get_response(
                            messages=message,
                            thread=thread
                        )
                        
                        # Validate the response content
                        if response and response.message and response.message.content:
                            if not self._validate_response_content(response.message.content):
                                raise ValueError("Invalid response content detected from Azure OpenAI")
                        
                        return response
                        
                    except Exception as e:
                        # Log the error with additional context
                        self.logger.error(f"OpenAI API call failed: {e}")
                        
                        # Check if this is the "invalid content" error specifically
                        if "invalid content" in str(e).lower():
                            self.logger.warning(
                                "Azure OpenAI returned 'invalid content' error. "
                                "This may be due to the model generating malformed output. "
                                "Consider adjusting the prompt or model parameters."
                            )
                            
                            # Record specific invalid content error - wrap in try-catch
                            try:
                                if 'openai_invalid_content_errors_total' in self.metrics:
                                    self.metrics['openai_invalid_content_errors_total'].add(1, {
                                        "model": self.deployment_name,
                                        "session_id": self.session_id
                                    })
                            except Exception as metric_e:
                                self.logger.warning(f"Failed to record invalid content error metric: {metric_e}")
                        
                        raise e
                
                # Use retry logic for the OpenAI call
                response = await self._retry_with_exponential_backoff(make_openai_call)
                thread = response.thread
                
                # Extract token usage from response if available - wrap in try-catch
                try:
                    # Try to access the underlying OpenAI response for token information
                    if hasattr(response, '_raw_response'):
                        raw_response = response._raw_response
                        add_token_span_attributes(raw_response, self.deployment_name)
                        record_token_metrics(raw_response, self.deployment_name, "chat_completion")
                    elif hasattr(response, 'usage'):
                        # If usage information is directly available
                        add_token_span_attributes(response, self.deployment_name)
                        record_token_metrics(response, self.deployment_name, "chat_completion")
                    else:
                        # If we can't find token info, at least log that we tried
                        self.logger.debug("Token usage information not found in response")
                        
                except Exception as e:
                    self.logger.warning(f"Could not extract token usage (operation continues): {e}")
                
                self.logger.info(f"Generated response for session: {self.session_id}")
        
        # Save chat history if CosmosDB is available
        if self.cosmos_manager:
            try:
                with TelemetryContext(operation="save_chat_history", session_id=self.session_id):
                    await self.cosmos_manager.save_chat_history(thread, self.session_id)
                    self.logger.info(f"Chat history saved with session ID: {self.session_id}")
                    
                    # Record successful save - wrap in try-catch
                    try:
                        if 'cosmosdb_operations_total' in self.metrics:
                            self.metrics['cosmosdb_operations_total'].add(1, {"operation": "save", "status": "success"})
                    except Exception as e:
                        self.logger.warning(f"Failed to record CosmosDB save success metric: {e}")
                        
            except Exception as e:
                self.logger.error(f"Error saving chat history: {e}")
                
                # Record failed save - wrap in try-catch
                try:
                    if 'cosmosdb_operations_total' in self.metrics:
                        self.metrics['cosmosdb_operations_total'].add(1, {"operation": "save", "status": "error"})
                except Exception as metric_error:
                    self.logger.warning(f"Failed to record CosmosDB save error metric: {metric_error}")

        return response.message.content

    def get_retry_configuration(self) -> dict:
        """
        Get the current retry configuration for monitoring and debugging.
        
        Returns:
            dict: Current retry configuration settings
        """
        is_o1_model = "o1" in self.deployment_name.lower() if self.deployment_name else False
        
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "jitter_enabled": self.jitter,
            "has_telemetry": self.telemetry is not None,
            "has_cosmosdb": self.cosmos_manager is not None,
            "session_id": self.session_id,
            "deployment_name": self.deployment_name,
            "is_o1_model": is_o1_model,
            "o1_optimizations_applied": is_o1_model,
            "max_response_length": int(os.getenv("MAX_RESPONSE_LENGTH", "100000" if is_o1_model else "50000"))
        }
    
    def get_health_status(self) -> dict:
        """
        Get the current health status of the agent and its dependencies.
        
        Returns:
            dict: Health status information
        """
        status = {
            "agent_initialized": True,
            "openai_configured": bool(self.endpoint and self.api_key and self.deployment_name),
            "telemetry_configured": self.telemetry is not None,
            "cosmosdb_configured": self.cosmos_manager is not None,
            "session_id": self.session_id,
            "retry_config": self.get_retry_configuration()
        }
        
        return status
