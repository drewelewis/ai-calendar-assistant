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
from semantic_kernel.contents import ChatMessageContent

from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager

from plugins.graph_plugin import GraphPlugin
from prompts.graph_prompts import prompts
 
load_dotenv(override=True)

class Agent:
    def __init__(self, session_id: str = None):
        
        self.session_id = session_id
        # 1. Load environment variables
        self.endpoint = os.getenv("OPENAI_ENDPOINT")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_version = os.getenv("OPENAI_API_VERSION")
        self.deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_database = os.getenv("COSMOS_DATABASE", "AIAssistant")
        self.cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
        
        # Validate required environment variables
        if not all([self.endpoint, self.api_key, self.deployment_name, self.cosmos_endpoint, self.cosmos_database, self.cosmos_container]):
            raise ValueError(
                "Missing required environment variables. Please ensure OPENAI_ENDPOINT, "
                "OPENAI_API_KEY, OPENAI_MODEL_DEPLOYMENT_NAME, COSMOS_ENDPOINT, "
                "COSMOS_DATABASE, and COSMOS_CONTAINER are set in the .env file."
            )

        try:
            self.cosmos_manager = CosmosDBChatHistoryManager(
                self.cosmos_endpoint, 
                self.cosmos_database, 
                self.cosmos_container
            )
        except Exception as e:
            print(f"Warning: Failed to initialize CosmosDB with Azure Identity: {e}")
            print("Chat history will not be persisted.")
            self.cosmos_manager = None
        
        # 2. Create the Kernel and register plugins
        self.service_id = "agent"
        self.kernel = Kernel()

        # 3. Add the Microsoft Graph plugin with optional debug mode
        self.graph_debug = os.getenv("GRAPH_DEBUG", "false").lower() == "true"
        self.kernel.add_plugin(GraphPlugin(debug=self.graph_debug), plugin_name="graph")
       
        # 4. Add Azure OpenAI service to the kernel
        self.kernel.add_service(AzureChatCompletion(
            deployment_name=self.deployment_name,
            endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version or "2023-05-15",
            service_id=self.service_id))
        
        self.settings = self.kernel.get_prompt_execution_settings_from_service_id(service_id=self.service_id)
        self.settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        # 5. Create the ChatCompletionAgent
        self.agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Agent",
            instructions=prompts.master_prompt(),
            arguments=KernelArguments(settings=self.settings),
        )

    async def invoke(self, message: str):
        # Create or hydrate thread based on CosmosDB availability
        if self.cosmos_manager:
            thread = await self.cosmos_manager.create_hydrated_thread(self.kernel, self.session_id)
        else:
            # Create a new empty thread if CosmosDB is not available
            from semantic_kernel.agents import ChatHistoryAgentThread
            thread = ChatHistoryAgentThread()
            
        response = await self.agent.get_response(
            messages=message,
            thread=thread,
        )
        thread = response.thread
        
        # Save chat history if CosmosDB is available
        if self.cosmos_manager:
            try:
                await self.cosmos_manager.save_chat_history(thread, self.session_id)
                print(f"Chat history saved with session ID: {self.session_id}")
            except Exception as e:
                print(f"Error saving chat history: {e}")

        return response.message.content



