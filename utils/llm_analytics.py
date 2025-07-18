"""
LLM Analytics and Cost Calculation Utilities
Provides detailed tracking and cost analysis for Azure OpenAI model usage.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

@dataclass
class TokenUsage:
    """Token usage information for a request."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def dict(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }

@dataclass
class ModelPricing:
    """Pricing information for Azure OpenAI models (per 1K tokens)."""
    input_cost_per_1k: float
    output_cost_per_1k: float
    model_name: str
    
class AzureOpenAIModels(Enum):
    """Azure OpenAI model pricing (USD per 1K tokens as of 2024)."""
    # GPT-4o models
    GPT_4O = ("gpt-4o", 0.005, 0.015)  # Input: $5/1M, Output: $15/1M
    GPT_4O_MINI = ("gpt-4o-mini", 0.00015, 0.0006)  # Input: $0.15/1M, Output: $0.6/1M
    
    # GPT-4 Turbo models
    GPT_4_TURBO = ("gpt-4-turbo", 0.01, 0.03)  # Input: $10/1M, Output: $30/1M
    GPT_4_TURBO_PREVIEW = ("gpt-4-turbo-preview", 0.01, 0.03)
    
    # GPT-4 models
    GPT_4 = ("gpt-4", 0.03, 0.06)  # Input: $30/1M, Output: $60/1M
    GPT_4_32K = ("gpt-4-32k", 0.06, 0.12)  # Input: $60/1M, Output: $120/1M
    
    # GPT-3.5 Turbo models
    GPT_35_TURBO = ("gpt-35-turbo", 0.0015, 0.002)  # Input: $1.5/1M, Output: $2/1M
    GPT_35_TURBO_16K = ("gpt-35-turbo-16k", 0.003, 0.004)  # Input: $3/1M, Output: $4/1M
    
    # Text Embedding models
    TEXT_EMBEDDING_ADA_002 = ("text-embedding-ada-002", 0.0001, 0.0001)  # $0.1/1M tokens
    TEXT_EMBEDDING_3_SMALL = ("text-embedding-3-small", 0.00002, 0.00002)  # $0.02/1M tokens
    TEXT_EMBEDDING_3_LARGE = ("text-embedding-3-large", 0.00013, 0.00013)  # $0.13/1M tokens
    
    def __init__(self, model_name: str, input_cost: float, output_cost: float):
        self.model_name = model_name
        self.input_cost_per_1k = input_cost
        self.output_cost_per_1k = output_cost
    
    @classmethod
    def get_model_pricing(cls, model_name: str) -> Optional['AzureOpenAIModels']:
        """Get pricing for a model by name."""
        for model in cls:
            if model.model_name.lower() in model_name.lower():
                return model
        return None

class LLMAnalytics:
    """LLM Analytics utility for cost calculation and token tracking."""
    
    def __init__(self):
        self.default_model = os.getenv("OPENAI_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
        
    def calculate_cost(self, 
                      token_usage: TokenUsage, 
                      model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate the cost for a given token usage.
        
        Args:
            token_usage: Token usage information
            model_name: Model name (defaults to environment variable)
            
        Returns:
            Dict containing detailed cost breakdown
        """
        model_name = model_name or self.default_model
        model_pricing = AzureOpenAIModels.get_model_pricing(model_name)
        
        if not model_pricing:
            # Default to GPT-4o-mini pricing if model not found
            model_pricing = AzureOpenAIModels.GPT_4O_MINI
            
        # Calculate costs (pricing is per 1K tokens)
        input_cost = (token_usage.prompt_tokens / 1000) * model_pricing.input_cost_per_1k
        output_cost = (token_usage.completion_tokens / 1000) * model_pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            "model_info": {
                "name": model_name,
                "detected_model": model_pricing.model_name,
                "input_rate_per_1k": f"${model_pricing.input_cost_per_1k:.6f}",
                "output_rate_per_1k": f"${model_pricing.output_cost_per_1k:.6f}"
            },
            "token_breakdown": {
                "prompt_tokens": token_usage.prompt_tokens,
                "completion_tokens": token_usage.completion_tokens,
                "total_tokens": token_usage.total_tokens,
                "token_efficiency": f"{(token_usage.completion_tokens / token_usage.total_tokens * 100):.1f}% output"
            },
            "cost_breakdown": {
                "input_cost": f"${input_cost:.6f}",
                "output_cost": f"${output_cost:.6f}",
                "total_cost": f"${total_cost:.6f}",
                "cost_per_token": f"${(total_cost / token_usage.total_tokens):.8f}" if token_usage.total_tokens > 0 else "$0.00000000"
            },
            "cost_summary": {
                "total_usd": round(total_cost, 6),
                "monthly_estimate_1k_calls": f"${(total_cost * 1000):.2f}",
                "daily_estimate_100_calls": f"${(total_cost * 100):.2f}"
            }
        }
    
    def format_analytics_display(self, 
                                cost_data: Dict[str, Any], 
                                session_id: str,
                                agent_type: str = "single") -> Dict[str, Any]:
        """
        Format analytics data for clear display in API responses.
        
        Args:
            cost_data: Cost calculation results
            session_id: Session identifier
            agent_type: Type of agent (single, multi_agent)
            
        Returns:
            Formatted analytics data
        """
        return {
            "📊 llm_analytics": {
                "🤖 model_details": {
                    "deployment_name": cost_data["model_info"]["name"],
                    "detected_model": cost_data["model_info"]["detected_model"],
                    "pricing_tier": {
                        "input_rate": cost_data["model_info"]["input_rate_per_1k"],
                        "output_rate": cost_data["model_info"]["output_rate_per_1k"]
                    }
                },
                "🔢 token_usage": {
                    "prompt_tokens": cost_data["token_breakdown"]["prompt_tokens"],
                    "completion_tokens": cost_data["token_breakdown"]["completion_tokens"],
                    "total_tokens": cost_data["token_breakdown"]["total_tokens"],
                    "efficiency": cost_data["token_breakdown"]["token_efficiency"]
                },
                "💰 cost_analysis": {
                    "input_cost": cost_data["cost_breakdown"]["input_cost"],
                    "output_cost": cost_data["cost_breakdown"]["output_cost"],
                    "total_cost": cost_data["cost_breakdown"]["total_cost"],
                    "cost_per_token": cost_data["cost_breakdown"]["cost_per_token"]
                },
                "📈 cost_projections": {
                    "current_call": cost_data["cost_summary"]["total_usd"],
                    "daily_100_calls": cost_data["cost_summary"]["daily_estimate_100_calls"],
                    "monthly_1k_calls": cost_data["cost_summary"]["monthly_estimate_1k_calls"]
                },
                "📋 session_info": {
                    "session_id": session_id[:12] + "..." if len(session_id) > 12 else session_id,
                    "agent_type": agent_type,
                    "timestamp": datetime.now().isoformat(),
                    "timezone": "UTC"
                }
            }
        }
    
    def extract_token_usage_from_response(self, response: Any) -> TokenUsage:
        """
        Extract token usage from various response formats.
        
        Args:
            response: Response object from OpenAI/Semantic Kernel
            
        Returns:
            TokenUsage object
        """
        token_usage = TokenUsage()
        
        # Try different response formats
        if hasattr(response, 'usage'):
            usage = response.usage
            token_usage.prompt_tokens = getattr(usage, 'prompt_tokens', 0)
            token_usage.completion_tokens = getattr(usage, 'completion_tokens', 0)
            token_usage.total_tokens = getattr(usage, 'total_tokens', 0)
        elif hasattr(response, 'token_usage'):
            usage = response.token_usage
            token_usage.prompt_tokens = getattr(usage, 'prompt_tokens', 0)
            token_usage.completion_tokens = getattr(usage, 'completion_tokens', 0)
            token_usage.total_tokens = getattr(usage, 'total_tokens', 0)
        elif isinstance(response, dict):
            # Handle dictionary responses
            if 'usage' in response:
                usage = response['usage']
                token_usage.prompt_tokens = usage.get('prompt_tokens', 0)
                token_usage.completion_tokens = usage.get('completion_tokens', 0)
                token_usage.total_tokens = usage.get('total_tokens', 0)
        
        # Calculate total if not provided
        if token_usage.total_tokens == 0 and (token_usage.prompt_tokens > 0 or token_usage.completion_tokens > 0):
            token_usage.total_tokens = token_usage.prompt_tokens + token_usage.completion_tokens
            
        return token_usage
    
    def get_model_comparison(self) -> Dict[str, Any]:
        """Get a comparison of available Azure OpenAI models and their pricing."""
        models = []
        
        for model in AzureOpenAIModels:
            models.append({
                "model_name": model.model_name,
                "input_cost_per_1k": f"${model.input_cost_per_1k:.6f}",
                "output_cost_per_1k": f"${model.output_cost_per_1k:.6f}",
                "cost_ratio": f"{model.output_cost_per_1k / model.input_cost_per_1k:.1f}x output",
                "use_case": self._get_model_use_case(model.model_name)
            })
        
        return {
            "available_models": models,
            "pricing_notes": [
                "Prices are per 1,000 tokens",
                "Actual costs may vary based on Azure region and subscription",
                "Embedding models typically charge the same for input and output",
                "Consider model capabilities vs. cost for your use case"
            ]
        }
    
    def _get_model_use_case(self, model_name: str) -> str:
        """Get recommended use case for a model."""
        if "gpt-4o-mini" in model_name:
            return "Fast, cost-effective for simple tasks"
        elif "gpt-4o" in model_name:
            return "Latest model, balanced performance and cost"
        elif "gpt-4-turbo" in model_name:
            return "Advanced reasoning, large context window"
        elif "gpt-4" in model_name:
            return "Complex reasoning, highest accuracy"
        elif "gpt-35-turbo" in model_name:
            return "Legacy model, basic conversational AI"
        elif "embedding" in model_name:
            return "Text embeddings for search and similarity"
        else:
            return "General purpose language model"

# Global instance
llm_analytics = LLMAnalytics()
