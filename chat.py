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

from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager

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



# Sample user inputs to demonstrate the AI calendar assistant functionality
# USER_INPUTS = [
#     "Logging in as user Id 12345678-1234-1234-1234-123456789abc",
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
# USER_INPUTS = [
#     "Where did we leave off? Please summarize our previous conversation."
# ]
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
        
        if cosmos_manager:
            try:
                session_id = await cosmos_manager.save_chat_history(thread, session_id)
                # print(f"Chat history saved with session ID: {session_id}")
            except Exception as e:
                print(f"Error saving chat history: {e}")

    # 8. Optional cleanup (you might want to keep history in CosmosDB instead)
    # await thread.delete() if thread else None
    print("Conversation completed. Chat history is stored in CosmosDB.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR RUNNING MAIN: {type(e).__name__}: {e}")