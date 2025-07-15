import re
from fastapi import FastAPI

from api.chat_completion import completion as api_chat_completion
from api.chat_completion import chat as api_chat
from models.openai_models import OpenAIModels
from ai.agent import Agent

app = FastAPI()

# Create input model for chat messages
from pydantic import BaseModel, Field


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/completion")
async def completion(query: str = "how are you?"):
    response=api_chat_completion(query)
    return response

@app.post("/chat")
async def chat(messages: OpenAIModels.Messages):
    message=api_chat(messages.messages)
    return message

@app.post("/agent_chat")
async def agent_chat(message: str):
    agent = Agent()
    result = await agent.invoke(message)
    return result