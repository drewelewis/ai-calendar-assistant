# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import uuid
from typing import Annotated
import datetime
import colorama
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential
from azure.core.exceptions import ClientAuthenticationError

from plugins.graph_plugin import GraphPlugin
from prompts.graph_prompts import prompts

"""
This file implements a chat assistant that integrates with Microsoft Graph API
to help users with calendar management and organization information.

The assistant uses Azure OpenAI to power the chat completion and Semantic Kernel
to handle the orchestration. GraphPlugin provides the Microsoft Graph functionality
for accessing organizational data and calendar operations.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response. The conversation history is
maintained in a ChatHistoryAgentThread object and persisted in Azure CosmosDB.
"""

class CosmosDBChatHistoryManager:
    """Manages chat history persistence with Azure Cosmos DB using Azure Identity."""
    
    def __init__(self, endpoint, database_name, container_name, credential=None):
        """
        Initialize the CosmosDB client using Azure Identity.
        
        Args:
            endpoint: CosmosDB endpoint URL
            database_name: Name of the database
            container_name: Name of the container
            credential: Optional Azure credential. If None, uses get_azure_credential()
        """
        if credential is None:
            # Use our custom credential getter with fallback options
            credential = get_azure_credential()
        
        self.client = CosmosClient(endpoint, credential=credential)
        self.database = self.client.create_database_if_not_exists(id=database_name)
        self.container = self.database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/sessionId"),
            offer_throughput=400  # Minimum throughput
        )
    
    async def save_chat_history(self, thread, session_id=None):
        """Save chat history from a thread to Cosmos DB."""
        if not thread:
            return
        
        # Generate a session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Extract messages from thread
        messages = []
        
        # Get the chat history from the thread
        try:
            # Handle different ways to access messages in Semantic Kernel
            thread_messages = []
            
            # Check if thread has messages attribute or property
            if hasattr(thread, 'messages'):
                # Handle async generator case
                if hasattr(thread.messages, '__aiter__'):
                    async_messages = thread.messages
                    async for message in async_messages:
                        thread_messages.append(message)
                else:
                    thread_messages = thread.messages
            # Try get_messages method
            elif hasattr(thread, 'get_messages'):
                get_messages_result = thread.get_messages()
                # Check if it's an async generator
                if hasattr(get_messages_result, '__aiter__'):
                    async for message in get_messages_result:
                        thread_messages.append(message)
                else:
                    thread_messages = get_messages_result
            # Try other possible attributes
            elif hasattr(thread, 'chat_history'):
                thread_messages = thread.chat_history
            elif hasattr(thread, 'history'):
                thread_messages = thread.history
            # Check if thread is dict-like with messages key
            elif isinstance(thread, dict) and "messages" in thread:
                thread_messages = thread["messages"]
                
            # Process all collected messages
            for message in thread_messages:
                if message.role.value == "user":
                    role = "user"
                elif message.role.value == "assistant":
                    role = "assistant"
                elif message.role.value == "system":
                    role = "system"
            
                # Enhanced content with function call details for CosmosDB storage
                # enhanced_content = self._create_enhanced_message_content(message)
                if hasattr(message, 'content'):
                    if message.content != "":
                        messages.append({
                            "role": role,
                            "content": message.content,
                            "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                        })

        except Exception as e:
            print(f"Warning: Could not extract messages from thread: {e}")
            # Continue with an empty messages list
            
        # Create document to store
        chat_history_document = {
            "id": str(uuid.uuid4()),
            "sessionId": session_id,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "messages": messages
        }
        
        # Save to Cosmos DB
        try:
            self.container.create_item(body=chat_history_document)
            return session_id
        except Exception as e:
            print(f"Error saving chat history to CosmosDB: {e}")
            # Re-raise the exception so calling code can handle it
            raise
        
    async def load_chat_history(self, session_id):
        """Load chat history from Cosmos DB and return the raw messages."""
        try:
            query = f"SELECT * FROM c WHERE c.sessionId = '{session_id}' ORDER BY c.timestamp DESC"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            
            if not items:
                print(f"No chat history found for session ID: {session_id}")
                return None
                
            # Take the most recent chat history
            chat_history = items[0]
            messages = chat_history.get("messages", [])
            
            print(f"Loaded chat history with {len(messages)} messages from {chat_history.get('timestamp', 'unknown time')}")
            
            # Return the raw messages - thread recreation will be handled by the calling code
            return messages
        except Exception as e:
            print(f"Error loading chat history from CosmosDB: {e}")
            return None

    def _create_enhanced_message_content(self, message):
        """
        Create minimal message content for CosmosDB storage.
        
        Args:
            message: The message object from Semantic Kernel
            
        Returns:
            str: Simple content string without verbose details
        """
        base_content = message.content or ""
        
        # Check for finish reason indicating function/tool calls
        finish_reason = None
        if hasattr(message, 'finish_reason'):
            finish_reason = message.finish_reason
        elif hasattr(message, 'metadata') and isinstance(message.metadata, dict):
            finish_reason = message.metadata.get('finish_reason')
        elif hasattr(message, 'additional_properties') and isinstance(message.additional_properties, dict):
            finish_reason = message.additional_properties.get('finish_reason')
        
        # If this message involves function/tool calls, just add a simple indicator
        if finish_reason and (
            (hasattr(finish_reason, 'value') and finish_reason.value in ["tool_calls", "function_call"]) or
            str(finish_reason).lower() in ["tool_calls", "function_call"]
        ):
            # Keep it extremely simple - just base content plus a simple function call indicator
            if base_content:
                return f"{base_content} [function calls executed]"
            else:
                return "[function calls executed]"
        
        # For non-function-call messages, return original content
        return base_content

    async def create_hydrated_thread(self, kernel, session_id):
        """
        Create a new ChatHistoryAgentThread and hydrate it with messages from CosmosDB.
        
        Args:
            kernel: The Semantic Kernel instance
            session_id: The session ID to load chat history for
            
        Returns:
            ChatHistoryAgentThread: A new thread with loaded messages, or empty thread if loading fails
        """
        from semantic_kernel.agents import ChatHistoryAgentThread
        from semantic_kernel.contents import ChatMessageContent, AuthorRole
        
        # Debug mode setting
        debug_mode = os.getenv("DEBUG_THREAD_API", "false").lower() == "true"
        
        # Create a new thread
        thread = ChatHistoryAgentThread()
        
        # Debug: Print available methods on the thread to understand the API
        if debug_mode:
            thread_methods = [method for method in dir(thread) if not method.startswith('_')]
            print(f"🐛 Available thread methods: {thread_methods}")
            if hasattr(thread, '_chat_history'):
                chat_history_methods = [method for method in dir(thread._chat_history) if not method.startswith('_')]
                print(f"🐛 Available chat_history methods: {chat_history_methods}")
        
        try:
            # Load previous messages
            previous_messages = await self.load_chat_history(session_id)
            if not previous_messages:
                return thread
            
            print(f"Hydrating thread with {len(previous_messages)} messages...")
            
            # Debug: Show what kind of thread we have
            if debug_mode:
                print(f"🐛 Thread type: {type(thread).__name__}")
            
            # Create ChatMessageContent objects and add them to the thread
            message_count = 0
            for i, stored_message in enumerate(previous_messages):
                try:
                    role = stored_message.get("role", "user")
                    content = stored_message.get("content", "")
                    timestamp = stored_message.get("timestamp", "unknown")
                    
                    # Skip empty messages
                    if not content.strip():
                        continue
                    
                    # Map role to AuthorRole
                    if role == "user":
                        author_role = AuthorRole.USER
                        print(f"  📝 Adding user message {i+1}: {content[:50]}...")
                    elif role == "assistant":
                        author_role = AuthorRole.ASSISTANT
                        print(f"  🤖 Adding assistant message {i+1}: {content[:50]}...")
                    elif role == "system":
                        author_role = AuthorRole.SYSTEM
                        print(f"  ⚙️  Adding system message {i+1}: {content[:50]}...")
                    else:
                        print(f"  ⚠️  Unknown message role '{role}', skipping message")
                        continue
                    
                    # Create a ChatMessageContent object
                    message = ChatMessageContent(
                        role=author_role,
                        content=content
                    )
                    
                    # Add the message to the thread using the proper API
                    try:
                        # Use add_chat_message if available (newer API)
                        if hasattr(thread, 'add_chat_message'):
                            thread.add_chat_message(message)
                            message_count += 1
                        # Fallback to add_message if available
                        elif hasattr(thread, 'add_message'):
                            thread.add_message(message)
                            message_count += 1
                        # Try accessing the chat history and add message there
                        elif hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'add_message'):
                            thread._chat_history.add_message(message)
                            message_count += 1
                        elif hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                            # If there's a messages list, append directly
                            thread._chat_history.messages.append(message)
                            message_count += 1
                        else:
                            print(f"  ⚠️  Unable to add message to thread - unknown chat history structure")
                    except Exception as msg_error:
                        print(f"  ❌ Error adding message to thread: {msg_error}")
                        # Try the direct approach as a last resort
                        try:
                            if hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                                thread._chat_history.messages.append(message)
                                message_count += 1
                        except Exception as fallback_error:
                            print(f"  ❌ Fallback approach also failed: {fallback_error}")
                        
                except Exception as e:
                    print(f"  ❌ Failed to add message {i+1} to thread: {e}")
                    if debug_mode:
                        print(f"  🐛 Message that failed: role={role}, content={content[:100]}...")
                        print(f"  🐛 Exception type: {type(e).__name__}")
                    continue
            
            print(f"Successfully hydrated thread with {message_count} messages")
            
            # Validate the hydration worked
            if debug_mode and message_count > 0:
                try:
                    # Try to verify messages were actually added
                    if hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                        actual_count = len(thread._chat_history.messages)
                        print(f"🐛 Verification: Thread now contains {actual_count} messages")
                    elif hasattr(thread, 'messages'):
                        # Handle async generator case
                        if hasattr(thread.messages, '__aiter__'):
                            count = 0
                            async for _ in thread.messages:
                                count += 1
                            print(f"🐛 Verification: Thread now contains {count} messages")
                        else:
                            actual_count = len(thread.messages) if hasattr(thread.messages, '__len__') else "unknown"
                            print(f"🐛 Verification: Thread now contains {actual_count} messages")
                except Exception as verify_error:
                    print(f"🐛 Could not verify thread hydration: {verify_error}")
            
            return thread
            
        except Exception as e:
            print(f"Error hydrating thread: {e}")
            print("Returning empty thread")
            return thread


# Sample user inputs to demonstrate the AI calendar assistant functionality
# USER_INPUTS = [
#     "Logging in as user Id 69149650-b87e-44cf-9413-db5c1a5b6d3f",
#     "Who is our CEO?",
#     "Can you get me the full org chart of our organization?",
#     "Can you get me a list of all departments in our organization?",
#     "Now can you help me schedule a meeting with the executive team?",
#     "I want everyone from the executive team to be invited.",
#     "The subject of the meeting will be quarterly results and future plans.",
#     "The body of the email will be about the quarterly results and future plans.",
#     "The meeting will have to be this Tuesday, in the morning if possible, for thirty minutes.",
#     "Before we schedule the meeting, can you verify the attendees and invite details you have so far?",
# ]
USER_INPUTS = [
    "Where did we leave off? Please summarize our previous conversation."
]

async def main():
    # Load environment variables
    load_dotenv(override=True)
    
    # 1. Create the instance of the Kernel to register an AI service
    endpoint = os.getenv("OPENAI_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    api_version = os.getenv("OPENAI_VERSION")
    deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")
    
    # Add CosmosDB configuration
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    # cosmos_key is no longer needed for AAD auth
    cosmos_database = os.getenv("COSMOS_DATABASE", "AIAssistant")
    cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
    
    # Validate required environment variables
    if not all([endpoint, api_key, deployment_name]):
        raise ValueError(
            "Missing required environment variables. Please ensure OPENAI_ENDPOINT, "
            "OPENAI_API_KEY, and OPENAI_MODEL_DEPLOYMENT_NAME are set in the .env file."
        )
    
    if not cosmos_endpoint:
        print("Warning: COSMOS_ENDPOINT environment variable not set. Chat history will not be persisted.")
        cosmos_manager = None
    else:
        # Initialize CosmosDB manager with Azure Identity
        try:
            cosmos_manager = CosmosDBChatHistoryManager(
                cosmos_endpoint, 
                cosmos_database, 
                cosmos_container
            )
            print("CosmosDB initialized with Azure Identity authentication")
        except Exception as e:
            print(f"Warning: Failed to initialize CosmosDB with Azure Identity: {e}")
            print("Chat history will not be persisted.")
            cosmos_manager = None
    
    # 2. Create the Kernel and register plugins
    service_id = "agent"
    kernel = Kernel()
    
    # Add the Microsoft Graph plugin with optional debug mode
    graph_debug = os.getenv("GRAPH_DEBUG", "false").lower() == "true"
    kernel.add_plugin(GraphPlugin(debug=graph_debug), plugin_name="graph")

    # 3. Add Azure OpenAI service to the kernel
    kernel.add_service(AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version or "2023-05-15",
        service_id=service_id))

    # 4. Configure the function choice behavior to auto invoke kernel functions
    # so that the agent can automatically execute Graph plugin functions when needed
    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # 5. Create the agent with the master prompt from graph_prompts
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Agent",
        instructions=prompts.master_prompt(),
        arguments=KernelArguments(settings=settings),
    )

    # 6. Create a thread to hold the conversation
    thread: ChatHistoryAgentThread = None
    
    # Optional: Load previous session
    session_id = os.getenv("CHAT_SESSION_ID")
    if cosmos_manager and session_id:
        # Try to load history from previous session
        try:
            print(f"Attempting to load previous chat session: {session_id}")
            thread = await cosmos_manager.create_hydrated_thread(kernel, session_id)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            print("Starting with a fresh conversation...")
            thread = ChatHistoryAgentThread()
    else:
        # Create a new thread if no session ID or cosmos manager
        thread = ChatHistoryAgentThread()

    # 7. Process each user input and get agent responses
    print("\nStarting conversation with the AI calendar assistant...\n")

    for user_input in USER_INPUTS:
        print(f"> User: {user_input}")
        print("")
        response = await agent.get_response(
            messages=user_input,
            thread=thread,
        )
        print(f"{colorama.Fore.LIGHTBLUE_EX}# {response.name}: {response}{colorama.Style.RESET_ALL} \n")
        thread = response.thread
        
        debug_mode = os.getenv("DEBUG_FINISH_REASON", "false").lower() == "true"
        # Check if response has finish_reason at the response level
        if debug_mode:
            if hasattr(response, 'finish_reason') and response.finish_reason:
                print(f"{colorama.Fore.LIGHTYELLOW_EX}📋 Response finish reason: {response.finish_reason}{colorama.Style.RESET_ALL}")
        
        # Debug: Print response attributes to understand structure
        
        if debug_mode:
            print(f"{colorama.Fore.LIGHTCYAN_EX}🐛 Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}{colorama.Style.RESET_ALL}")
        
        if debug_mode:
            for message in response.thread._chat_history.messages:
                # Debug: Print message attributes to understand structure
                print(f"{colorama.Fore.LIGHTCYAN_EX}🐛 Message attributes: {[attr for attr in dir(message) if not attr.startswith('_')]}{colorama.Style.RESET_ALL}")
            
            # # Check for finish reason on the message
            # finish_reason = None
            
            # # Try different ways to access finish_reason
            # if hasattr(message, 'finish_reason'):
            #     finish_reason = message.finish_reason
            # elif hasattr(message, 'metadata') and isinstance(message.metadata, dict):
            #     finish_reason = message.metadata.get('finish_reason')
            # elif hasattr(message, 'additional_properties') and isinstance(message.additional_properties, dict):
            #     finish_reason = message.additional_properties.get('finish_reason')
            
            # # Print message with finish reason information
            # if finish_reason:
            #     if finish_reason.value == "tool_calls":
            #         # Create enhanced content for display (similar to CosmosDB storage)
            #         enhanced_display_content = create_enhanced_display_content(message)
            #         if enhanced_display_content:
            #             message.content = enhanced_display_content
            #             message.role = "tool"  # Update role to tool for clarity
            #         print(f"{colorama.Fore.LIGHTBLUE_EX}# {message.role.value}: {enhanced_display_content}{colorama.Style.RESET_ALL}")
            #     else:
            #         print(f"{colorama.Fore.LIGHTCYAN_EX}# {message.role.value}: {message.content}{colorama.Style.RESET_ALL}")
            #     print_finish_reason_info(finish_reason.value)
            #     print()  # Add extra line for better readability
            # else:
            #     print(f"{colorama.Fore.LIGHTGREEN_EX}# {message.role.value}: {message.content}{colorama.Style.RESET_ALL} \n")

        # Save chat history to CosmosDB after each response
        if cosmos_manager:
            try:
                session_id = await cosmos_manager.save_chat_history(thread, session_id)
                # print(f"Chat history saved with session ID: {session_id}")
            except Exception as e:
                print(f"Error saving chat history: {e}")

    # 8. Optional cleanup (you might want to keep history in CosmosDB instead)
    # await thread.delete() if thread else None
    print("Conversation completed. Chat history is stored in CosmosDB.")


def get_azure_credential():
    """
    Get Azure credentials with fallback options.
    Tries multiple authentication methods in order of preference:
    1. Environment variables (for CI/CD)
    2. Managed Identity (for Azure-hosted applications)
    3. DefaultAzureCredential (interactive/local development)
    """
    try:
        # Try environment credential first (good for CI/CD)
        credential = EnvironmentCredential()
        # Test the credential
        credential.get_token("https://cosmos.azure.com/.default")
        return credential
    except Exception:
        pass
    
    try:
        # Try managed identity (good for Azure-hosted apps)
        credential = ManagedIdentityCredential()
        # Test the credential
        credential.get_token("https://cosmos.azure.com/.default")
        return credential
    except Exception:
        pass
    
    try:
        # Fall back to DefaultAzureCredential (includes interactive auth)
        credential = DefaultAzureCredential(exclude_visual_studio_code_credential=False)
        # Test the credential
        credential.get_token("https://cosmos.azure.com/.default")
        return credential
    except Exception as e:
        raise ClientAuthenticationError(
            f"Failed to authenticate with Azure. Please ensure you are logged in via Azure CLI "
            f"or have appropriate credentials configured. Error: {e}"
        )


def print_finish_reason_info(finish_reason):
    """Print informative finish reason details with appropriate colors and descriptions."""
    if not finish_reason:
        return
    
    finish_reason_descriptions = {
        "stop": "✅ Normal completion - The model finished generating the response naturally",
        "length": "⚠️  Length limit - The response was cut off due to maximum token limit",
        "function_call": "🔧 Function call - The model wants to call a function",
        "tool_calls": "🛠️  Tool calls - The model wants to call one or more tools",
        "content_filter": "🚫 Content filter - Response was filtered due to content policy",
        "null": "❓ Unknown - Finish reason is null or undefined"
    }
    
    # Normalize finish reason to string and lowercase
    reason_str = str(finish_reason).lower() if finish_reason else "null"
    
    # Get description or use default
    description = finish_reason_descriptions.get(reason_str, f"❓ Unknown reason: {finish_reason}")
    
    # Choose color based on finish reason
    if reason_str == "stop":
        color = colorama.Fore.LIGHTGREEN_EX
    elif reason_str in ["function_call", "tool_calls"]:
        color = colorama.Fore.LIGHTBLUE_EX
    elif reason_str == "length":
        color = colorama.Fore.LIGHTYELLOW_EX
    elif reason_str == "content_filter":
        color = colorama.Fore.LIGHTRED_EX
    else:
        color = colorama.Fore.LIGHTMAGENTA_EX
    
    print(f"  {color}🏁 {description}{colorama.Style.RESET_ALL}")


def create_enhanced_display_content(message):
    """
    Create enhanced display content for function calls during console output.
    
    Args:
        message: The message object from Semantic Kernel
        
    Returns:
        str: Enhanced content string for display
    """
    base_content = message.content or ""
    
    # Create a concise but informative display
    display_parts = [f"Content: {base_content}"]
    
    # Check for function call details
    function_calls_found = False
    
    # Check for function_call attribute (single function call)
    if hasattr(message, 'function_call'):
        function_call = message.function_call
        function_calls_found = True
        display_parts.append(f"Function Call: {getattr(function_call, 'name', 'unknown')}")
        
        if hasattr(function_call, 'arguments'):
            try:
                args = function_call.arguments
                if isinstance(args, str):
                    try:
                        args_dict = json.loads(args)
                        display_parts.append(f"   Arguments: {json.dumps(args_dict, indent=3)}")
                    except json.JSONDecodeError:
                        display_parts.append(f"   Arguments: {args}")
                else:
                    display_parts.append(f"   Arguments: {json.dumps(args, indent=3, default=str)}")
            except Exception as e:
                display_parts.append(f"   Arguments: (Error: {e})")
        
        if hasattr(function_call, 'output'):
            try:
                output = function_call.output
                if output is not None:
                    display_parts.append(f"   Output: {json.dumps(output, indent=3, default=str)}")
            except Exception as e:
                display_parts.append(f"   Output: (Error: {e})")
    
    # Check for tool_calls attribute (multiple tool calls)
    if hasattr(message, 'tool_calls'):
        for i, tool_call in enumerate(message.tool_calls, 1):
            function_calls_found = True
            func_name = "unknown"
            if hasattr(tool_call, 'function'):
                func_name = tool_call.function.get('name', 'unknown') if isinstance(tool_call.function, dict) else getattr(tool_call.function, 'name', 'unknown')
            
            display_parts.append(f"Tool Call {i}: {func_name}")
            
            # Add tool call ID if available
            if hasattr(tool_call, 'id'):
                display_parts.append(f"Call ID: {tool_call.id}")
    
    # Check for items attribute (Semantic Kernel specific)
    if hasattr(message, 'items') and message.items:
        function_calls_found = True
        try:
            display_parts.append(f"Function Items: {json.dumps(message.items, indent=3, default=str)}")
        except Exception as e:
            display_parts.append(f"Function Items: (Error: {e})")
    
    # If no function calls found but this is supposed to be a tool call, show basic info
    if not function_calls_found:
        display_parts.append("Tool call detected but details not accessible")
    
    return "\n".join(display_parts)


async def test_state_hydration():
    """
    Test function to verify state hydration is working correctly.
    This function will create some test messages, save them, and then reload them.
    """
    try:
        load_dotenv(override=True)
        
        # Get CosmosDB configuration
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        cosmos_database = os.getenv("COSMOS_DATABASE", "AIAssistant")
        cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
        
        if not cosmos_endpoint:
            print("❌ COSMOS_ENDPOINT not set, cannot test state hydration")
            return False
        
        # Initialize CosmosDB manager
        cosmos_manager = CosmosDBChatHistoryManager(
            cosmos_endpoint, 
            cosmos_database, 
            cosmos_container
        )
        
        # Create a test session ID
        test_session_id = f"test-{uuid.uuid4()}"
        
        # Create test messages
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant.", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()},
            {"role": "user", "content": "Hello, can you help me?", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()},
            {"role": "assistant", "content": "Of course! I'm here to help you.", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()},
            {"role": "user", "content": "What's the weather like?", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()}
        ]
        
        # Save test messages to CosmosDB
        print(f"💾 Saving test messages to session: {test_session_id}")
        chat_history_document = {
            "id": str(uuid.uuid4()),
            "sessionId": test_session_id,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "messages": test_messages
        }
        cosmos_manager.container.create_item(body=chat_history_document)
        print(f"✅ Saved {len(test_messages)} test messages")
        
        # Try to load and hydrate
        print(f"🔄 Loading messages from session: {test_session_id}")
        loaded_messages = await cosmos_manager.load_chat_history(test_session_id)
        
        if loaded_messages:
            print(f"✅ Successfully loaded {len(loaded_messages)} messages")
            
            # Create a minimal kernel for testing
            from semantic_kernel import Kernel
            kernel = Kernel()
            
            # Test hydration
            print("🧪 Testing thread hydration...")
            thread = await cosmos_manager.create_hydrated_thread(kernel, test_session_id)
            
            if thread:
                print("✅ Thread hydration completed successfully!")
                return True
            else:
                print("❌ Thread hydration failed")
                return False
        else:
            print("❌ Failed to load messages")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Check for test command
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Running state hydration test...")
        try:
            result = asyncio.run(test_state_hydration())
            if result:
                print("✅ State hydration test passed!")
            else:
                print("❌ State hydration test failed!")
        except Exception as e:
            print(f"❌ Test error: {e}")
    else:
        # Run normal chat application
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"ERROR RUNNING MAIN: {type(e).__name__}: {e}")