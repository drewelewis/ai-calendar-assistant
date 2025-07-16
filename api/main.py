import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat_completion import completion as api_chat_completion
from api.chat_completion import chat as api_chat
from models.openai_models import OpenAIModels
from models.chat_models import ChatModels
from ai.agent import Agent

# Import telemetry components
from telemetry.config import initialize_telemetry, get_telemetry
from telemetry.decorators import trace_async_method, measure_performance
import os

# Initialize telemetry for FastAPI
connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant")
service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")

telemetry = initialize_telemetry(
    service_name=service_name,
    service_version=service_version
)

app = FastAPI(
    title="AI Calendar Assistant API",
    description="Azure OpenAI powered calendar assistant with Microsoft Graph integration",
    version=service_version
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create input model for chat messages
from pydantic import BaseModel, Field


@app.get("/health")
@trace_async_method(operation_name="api.health_check")
async def health_check():
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info("Health check requested")
    return {"status": "ok", "service": service_name, "version": service_version}

@app.get("/completion")
@trace_async_method(operation_name="api.completion")
@measure_performance("api_completion")
async def completion(query: str = "how are you?"):
    response=api_chat_completion(query)
    return response

@app.post("/chat")
@trace_async_method(operation_name="api.chat")
@measure_performance("api_chat")
async def chat(messages: OpenAIModels.Messages):
    message=api_chat(messages.messages)
    return message

@app.post("/agent_chat")
@trace_async_method(operation_name="api.agent_chat", include_args=True)
@measure_performance("api_agent_chat")
async def agent_chat(message: ChatModels.Message):
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info(f"Agent chat request for session: {message.session_id}")
    
    agent = Agent(session_id=message.session_id)
    result = await agent.invoke(message.message)
    return result