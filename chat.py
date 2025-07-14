# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import uuid
from typing import Annotated
import datetime

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
                elif message.role.value == "function":
                    role = "function"
                elif message.role.value == "system":
                    role = "system"
            

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
        """Load chat history from Cosmos DB and create a new thread."""
        try:
            query = f"SELECT * FROM c WHERE c.sessionId = '{session_id}' ORDER BY c.timestamp DESC"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            
            if not items:
                return None
                
            # Take the most recent chat history
            chat_history = items[0]
            
            # Return the raw messages - thread recreation will be handled by the calling code
            return chat_history["messages"]
        except Exception as e:
            print(f"Error loading chat history from CosmosDB: {e}")
            return None

# Sample user inputs to demonstrate the AI calendar assistant functionality
USER_INPUTS = [
    "Logging in as user Id 69149650-b87e-44cf-9413-db5c1a5b6d3f",
    # "Who is our CEO?",
    # "Can you get me the full org chart of our organization?",
    # "Can you get me a list of all departments in our organization?",
    "Now can you help me schedule a meeting with the executive team?",
    "I want everyone from the executive team to be invited.",
    "The subject of the meeting will be quarterly results and future plans.",
    "The body of the email will be about the quarterly results and future plans.",
    "The meeting will have to be this Tuesday, in the morning if possible, for thirty minutes.",
    "Before we schedule the meeting, can you verify the attendees and invite details you have so far?",
]


async def main():
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
            previous_messages = await cosmos_manager.load_chat_history(session_id)
            if previous_messages:
                print(f"Loaded previous chat session: {session_id}")
                # Note: Implementation of recreating thread from messages depends on SK API
                # This is a placeholder for that logic - you would need to implement the 
                # conversion from stored messages to SK's thread format
        except Exception as e:
            print(f"Error loading chat history: {e}")

    # 7. Process each user input and get agent responses
    print("\nStarting conversation with the AI calendar assistant...\n")

    for user_input in USER_INPUTS:
        print(f"> User: {user_input}")
        print("")
        response = await agent.get_response(
            messages=user_input,
            thread=thread,
        )
        print(f"# {response.name}: {response} \n")
        thread = response.thread
        
        # Save chat history to CosmosDB after each response
        if cosmos_manager:
            try:
                session_id = await cosmos_manager.save_chat_history(thread, session_id)
                print(f"Chat history saved with session ID: {session_id}")
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


if __name__ == "__main__":
    try:
            asyncio.run(main())
    except Exception as e:
        print(f"ERROR RUNNING MAIN: {type(e).__name__}: {e}")