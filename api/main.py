import re
from fastapi import FastAPI

from api import chat_completion
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
    response=chat_completion.completion(query)
    return response

@app.post("/chat")
async def chat(messages: OpenAIModels.Messages):
    message=chat_completion.chat(messages.messages)
    return message

@app.post("/agent_chat")
async def agent_chat(messages: OpenAIModels.Messages):
    agent = Agent()
    result = agent.invoke_graph(messages.messages)
    return result