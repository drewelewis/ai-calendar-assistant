import re
from urllib import request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat_completion import completion as api_chat_completion
from api.chat_completion import chat as api_chat
from models.openai_models import OpenAIModels
from models.chat_models import ChatModels
from ai.agent import Agent
from ai.multi_agent import MultiAgentOrchestrator
from utils.llm_analytics import llm_analytics, TokenUsage
from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager

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
    
    # Extract token usage for cost analysis
    token_usage = llm_analytics.extract_token_usage_from_response(result)
    
    # Calculate costs and analytics
    cost_data = llm_analytics.calculate_cost(token_usage)
    analytics = llm_analytics.format_analytics_display(cost_data, message.session_id, "single_agent")
    
    return {
        "response": result.content if hasattr(result, 'content') else str(result),
        "session_id": message.session_id,
        "agent_type": "single_agent",
        **analytics
    }

@app.post("/multi_agent_chat")
@trace_async_method(operation_name="api.multi_agent_chat", include_args=True)
@measure_performance("api_multi_agent_chat")
async def multi_agent_chat(message: ChatModels.Message):
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info(f"Multi-agent chat request for session: {message.session_id}")
    
    try:
        # Validate session_id is provided
        if not message.session_id:
            logger.error("Session ID is required for multi-agent chat")
            return {
                "error": "Session ID is required",
                "message": "Please provide a valid session_id in your request"
            }
        
        # Create multi-agent orchestrator with required session_id
        orchestrator = MultiAgentOrchestrator(session_id=message.session_id)
        
        # Process message through multi-agent system
        result = await orchestrator.process_message(message.message)
        
        # For multi-agent, we'll estimate token usage based on response length
        # In a production system, you'd want to modify the orchestrator to return token usage
        estimated_tokens = TokenUsage(
            prompt_tokens=len(message.message.split()) * 1.3,  # Rough estimate
            completion_tokens=len(result.split()) * 1.3,  # Rough estimate
            total_tokens=(len(message.message.split()) + len(result.split())) * 1.3
        )
        
        # Calculate costs and analytics
        cost_data = llm_analytics.calculate_cost(estimated_tokens)
        analytics = llm_analytics.format_analytics_display(cost_data, message.session_id, "multi_agent")
        
        return {
            "response": result,
            "session_id": message.session_id,
            "agent_type": "multi_agent",
            "note": "Token usage estimated for multi-agent system",
            **analytics
        }
        
    except ValueError as ve:
        # Handle session_id validation errors
        logger.error(f"Multi-agent validation error: {ve}")
        return {
            "error": "Validation Error", 
            "message": str(ve)
        }
    except Exception as e:
        # Handle other errors
        logger.error(f"Multi-agent chat error: {e}")
        return {
            "error": "Processing Error",
            "message": "An error occurred while processing your request. Please try again."
        }

@app.get("/multi_agent_status")
@trace_async_method(operation_name="api.multi_agent_status")
async def multi_agent_status(session_id: str):
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info(f"Multi-agent status request for session: {session_id}")
    
    try:
        # Validate session_id is provided
        if not session_id:
            return {
                "error": "Session ID is required",
                "message": "Please provide a valid session_id parameter"
            }
        
        # Create multi-agent orchestrator to get status
        orchestrator = MultiAgentOrchestrator(session_id=session_id)
        status = await orchestrator.get_agent_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except ValueError as ve:
        # Handle session_id validation errors
        logger.error(f"Multi-agent status validation error: {ve}")
        return {
            "error": "Validation Error", 
            "message": str(ve)
        }
    except Exception as e:
        # Handle other errors
        logger.error(f"Multi-agent status error: {e}")
        return {
            "error": "Status Error",
            "message": "An error occurred while retrieving agent status. Please try again."
        }

@app.get("/llm_models")
@trace_async_method(operation_name="api.llm_models")
async def get_llm_models():
    """Get available Azure OpenAI models and their pricing information."""
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info("LLM models and pricing request")
    
    try:
        model_comparison = llm_analytics.get_model_comparison()
        
        return {
            "status": "success",
            "data": {
                "🤖 azure_openai_models": model_comparison["available_models"],
                "💡 pricing_information": {
                    "currency": "USD",
                    "unit": "per 1,000 tokens",
                    "notes": model_comparison["pricing_notes"],
                    "current_deployment": os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME", "Not configured"),
                    "last_updated": "2024-Q4"
                },
                "📊 cost_calculator": {
                    "description": "Use /calculate_cost endpoint to estimate costs for specific usage",
                    "example": "POST /calculate_cost with token counts"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving LLM models: {e}")
        return {
            "error": "Models Error",
            "message": "An error occurred while retrieving model information."
        }

@app.post("/calculate_cost")
@trace_async_method(operation_name="api.calculate_cost")
async def calculate_cost(request: dict):
    """
    Calculate cost for specific token usage.
    
    Request body:
    {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "model_name": "gpt-4o-mini"  // optional
    }
    """
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info("Cost calculation request")
    
    try:
        # Extract token information
        prompt_tokens = request.get("prompt_tokens", 0)
        completion_tokens = request.get("completion_tokens", 0)
        model_name = request.get("model_name")
        
        if prompt_tokens <= 0 and completion_tokens <= 0:
            return {
                "error": "Invalid Input",
                "message": "Please provide valid prompt_tokens and/or completion_tokens"
            }
        
        # Create token usage object
        token_usage = TokenUsage(
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            total_tokens=int(prompt_tokens) + int(completion_tokens)
        )
        
        # Calculate costs
        cost_data = llm_analytics.calculate_cost(token_usage, model_name)
        
        return {
            "status": "success",
            "calculation": {
                "🔢 input_tokens": prompt_tokens,
                "🔢 output_tokens": completion_tokens,
                "🔢 total_tokens": token_usage.total_tokens,
                "🤖 model_used": cost_data["model_info"]["detected_model"],
                "💰 cost_breakdown": cost_data["cost_breakdown"],
                "📈 projections": cost_data["cost_summary"],
                "⚡ efficiency": cost_data["token_breakdown"]["token_efficiency"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating cost: {e}")
        return {
            "error": "Calculation Error",
            "message": "An error occurred while calculating costs."
        }
# clear chat history endpoint
@app.post("/clear_chat_history")
@trace_async_method(operation_name="api.clear_chat_history")
async def clear_chat_history(session: ChatModels.Session):
    """Clear chat history for the user
    Request body:
    {
        "session_id": "abcd1234-5678-90ef-ghij-klmnopqrstuv"  # required, if you want to clear history for a specific session

    }
    """
    # get session_id from request body
    session_id = session.session_id
    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info("Clear chat history request")
    
    try:
        # TODO: Implement chat history clearing logic here
        # For now, return success as placeholder
        # This should call CosmosDBChatHistoryManager or similar to clear history
        cosmos_manager = await get_cosmos_manager()
        # Clear chat history for a specific session or all sessions
        # For example, clear history for a specific session ID
        await cosmos_manager.clear_chat_history(session_id=session_id)  # Pass session_id if needed
        return {
            "status": "success",
            "message": "Chat history cleared successfully."
        }
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return {
            "error": "Clear History Error",
            "message": "An error occurred while clearing chat history."
        }   

async def get_cosmos_manager():
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    cosmos_database = os.getenv("COSMOS_DATABASE", "AIAssistant")
    cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")

    logger = get_telemetry().get_logger() if get_telemetry() else None
    if logger:
        logger.info(f"Getting CosmosDBChatHistoryManager with endpoint: {cosmos_endpoint}, database: {cosmos_database}, container: {cosmos_container}")

    # Initialize CosmosDBChatHistoryManager
    cosmos_manager = CosmosDBChatHistoryManager(
        endpoint=cosmos_endpoint,
        database_name=cosmos_database,
        container_name=cosmos_container
    )

    return cosmos_manager

        