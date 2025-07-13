# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from dotenv import load_dotenv

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

"""
The following sample demonstrates how to create a chat completion agent that
answers user questions using the Azure Chat Completion service. The Chat Completion
Service is passed directly via the ChatCompletionAgent constructor. This sample
demonstrates the basic steps to create an agent and simulate a conversation
with the agent.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent.
"""

# Simulate a conversation with the agent
USER_INPUTS = [
    "Why is the sky blue?",
    "My name is Jim, what is my name?",
    "what is my name?"
]


async def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get Azure OpenAI configuration from environment variables
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
    
    # 1. Create the agent by specifying the service with proper configuration
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version or "2023-05-15"
        ),
        name="Assistant",
        instructions="Answer questions about the world in one sentence.",
    )

    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        # 2. Invoke the agent for a response
        response = await agent.get_response(
            messages=user_input,
        )
        # 3. Print the response
        print(f"# {response.name}: {response}")

    """
    Sample output:
    # User: Why is the sky blue?
    # Assistant: The sky appears blue because molecules in the Earth's atmosphere scatter shorter wavelengths of 
        sunlight, like blue, more than the longer wavelengths, causing the sky to look blue to our eyes.
    # User: What is the capital of France?
    # Assistant: The capital of France is Paris.
    """


if __name__ == "__main__":
    asyncio.run(main())