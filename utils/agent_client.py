# Copyright (c) Microsoft. All rights reserved.
"""
Azure OpenAI client configuration for Microsoft Agent Framework.
Provides a configured ChatClient instance for all Agent Framework agents.
"""
import os
from dotenv import load_dotenv
from azure.ai.agents.client.chat import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

load_dotenv(override=True)


def create_agent_chat_client() -> AzureOpenAIChatClient:
    """
    Create and configure an AzureOpenAIChatClient for Agent Framework.
    
    Returns:
        AzureOpenAIChatClient configured with environment variables
    """
    endpoint = os.getenv("OPENAI_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    api_version = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")
    deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME")

    if not endpoint or not deployment_name:
        raise ValueError(
            "Missing required environment variables: "
            "OPENAI_ENDPOINT and OPENAI_MODEL_DEPLOYMENT_NAME must be set"
        )

    # Use API key if provided, otherwise fall back to DefaultAzureCredential
    if api_key:
        client = AzureOpenAIChatClient(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            model=deployment_name,
        )
    else:
        credential = DefaultAzureCredential()
        client = AzureOpenAIChatClient(
            endpoint=endpoint,
            credential=credential,
            api_version=api_version,
            model=deployment_name,
        )

    return client


def get_model_settings() -> dict:
    """
    Get model execution settings from environment variables.
    
    Returns:
        Dictionary of model settings (max_tokens, temperature, top_p)
    """
    deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME", "")
    is_o1 = "o1" in deployment_name.lower()
    
    settings = {
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "8000")),
    }
    
    # o1 models don't support temperature/top_p
    if not is_o1:
        settings["temperature"] = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        settings["top_p"] = float(os.getenv("OPENAI_TOP_P", "0.9"))
    
    return settings


def get_router_settings() -> dict:
    """
    Get optimized model settings for the LLM router.
    Router needs minimal tokens and deterministic responses.
    
    Returns:
        Dictionary of router-specific settings
    """
    deployment_name = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME", "")
    is_o1 = "o1" in deployment_name.lower()
    
    settings = {
        "max_tokens": 10,  # Router only returns a single word
    }
    
    if not is_o1:
        settings["temperature"] = 0.0  # Deterministic routing
    
    return settings
