# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import uuid
import logging
from typing import Annotated
import datetime
import colorama
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager

from plugins.graph_plugin import GraphPlugin
from prompts.graph_prompts import prompts

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
        
        # 2. Create the Kernel and register plugins
        self.service_id = "agent"
        self.kernel = Kernel()

        # 3. Add the Microsoft Graph plugin with optional debug mode
        self.graph_debug = os.getenv("GRAPH_DEBUG", "false").lower() == "true"
        self.kernel.add_plugin(GraphPlugin(debug=self.graph_debug), plugin_name="graph")
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
        
        self.settings = self.kernel.get_prompt_execution_settings_from_service_id(service_id=self.service_id)
        self.settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        # Create agent with properly structured instructions
        combined_instructions = prompts.build_complete_instructions(self.session_id)

        self.agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Agent",
            instructions=combined_instructions,
            arguments=KernelArguments(settings=self.settings),
        )
        
        self.logger.info("✅ AI Calendar Assistant Agent initialized successfully")


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
            
            
            # Check if we need to add initial messages (system and instructions)
            has_system_message = False
            
            try:
                # Get messages from the thread using the proper API
                messages = []
                
                # Try different ways to access the message history
                if hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                    messages = thread._chat_history.messages
                elif hasattr(thread, 'messages'):
                    # Handle async generator case
                    if hasattr(thread.messages, '__aiter__'):
                        async for msg in thread.messages:
                            messages.append(msg)
                    elif hasattr(thread.messages, '__iter__'):
                        # Handle iterable case
                        messages = list(thread.messages)
                    else:
                        messages = thread.messages
                
                # Evaluate messages list to determine if we have a system message
                # look at messages for a message with the role of SYSTEM

                if any(msg.role == AuthorRole.SYSTEM for msg in messages):
                    self.logger.debug("Found existing system message in thread")
                    has_system_message = True
                else:
                    self.logger.debug("No existing system message found in thread")
                    has_system_message = False
                
            except Exception as e:
                self.logger.debug(f"Could not check existing messages: {e}")
                # Default to adding messages if we can't check
                has_system_message = False

            # Add system message and instructions if needed
            if has_system_message== False:
                def add_message_to_thread(message, message_type):
                    """Helper function to add a message to the thread using available methods"""
                    try:
                        if hasattr(thread, 'add_chat_message'):
                            thread.add_chat_message(message)
                            self.logger.debug(f"Added {message_type} using add_chat_message")
                        elif hasattr(thread, 'add_message'):
                            thread.add_message(message)
                            self.logger.debug(f"Added {message_type} using add_message")
                        elif hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'add_message'):
                            thread._chat_history.add_message(message)
                            self.logger.debug(f"Added {message_type} using _chat_history.add_message")
                        elif hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                            thread._chat_history.messages.append(message)
                            self.logger.debug(f"Added {message_type} by appending to messages list")
                        else:
                            self.logger.warning(f"Could not find method to add {message_type} to thread")
                    except Exception as e:
                        self.logger.error(f"Failed to add {message_type} to thread: {e}")

                # Add system message
                system_message = ChatMessageContent(
                    role=AuthorRole.SYSTEM, 
                    content=prompts.system_message(self.session_id)
                )
                add_message_to_thread(system_message, "system message")

                # Add instruction message with the system message
                instruction_message = ChatMessageContent(
                    role=AuthorRole.USER, 
                    content=prompts.instructions(self.session_id)
                )
                add_message_to_thread(instruction_message, "instruction message")

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
                
                response = await self.agent.get_response(
                    messages=message,
                    thread=thread
                )
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



