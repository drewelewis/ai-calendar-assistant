# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior

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
maintained in a ChatHistoryAgentThread object.
"""

# Sample user inputs to demonstrate the AI calendar assistant functionality
USER_INPUTS = [
    "Logging in as user Id 69149650-b87e-44cf-9413-db5c1a5b6d3f",
    "Who is our CEO?",
    "Can you get me the full org chart of our organization?",
    "Now can you help me schedule a meeting with the executive team?",
    "Yes, these are the folks I want to be included.",
    "The meeting will have to be this Tuesday, in the morning if possible.",
    "I want to meet for 30 minutes.",
]


async def main():
    # 1. Create the instance of the Kernel to register an AI service
    endpoint = os.getenv("OPENAI_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    api_version = os.getenv("OPENAI_VERSION")
    deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")
    
    # Validate required environment variables
    if not all([endpoint, api_key, deployment_name]):
        raise ValueError(
            "Missing required environment variables. Please ensure OPENAI_ENDPOINT, "
            "OPENAI_API_KEY, and OPENAI_MODEL_DEPLOYMENT_NAME are set in the .env file."
        )
    
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

    # 7. Process each user input and get agent responses
    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        response = await agent.get_response(
            messages=user_input,
            thread=thread,
        )
        print(f"# {response.name}: {response}")
        thread = response.thread

    # 8. Cleanup: Clear the thread
    await thread.delete() if thread else None

    """
    Sample output would include responses related to:
    - Authentication confirmation
    - Organizational information (CEO details)
    - Organization chart data
    - Meeting scheduling with executive team
    - Meeting time and duration confirmation
    """


if __name__ == "__main__":
    asyncio.run(main())