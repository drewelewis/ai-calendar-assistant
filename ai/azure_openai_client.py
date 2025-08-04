import os
import openai
from typing import List, Dict, Any


class OpenAIClient:
    def __init__(self):
        """Initialize Azure OpenAI client with environment variables."""
        # Check if the environment variables are set
        azure_endpoint = os.environ.get("OPENAI_ENDPOINT")
        if azure_endpoint is None:
            raise ValueError("Please set the environment variable 'OPENAI_ENDPOINT' to your Azure OpenAI endpoint.")
        
        azure_api_key = os.environ.get("OPENAI_API_KEY")
        if azure_api_key is None:
            raise ValueError("Please set the environment variable 'OPENAI_API_KEY' to your Azure OpenAI API key.")
        
        api_version = os.environ.get("OPENAI_VERSION")
        if api_version is None:
            raise ValueError("Please set the environment variable 'OPENAI_VERSION' to your Azure OpenAI API version.")
        
        model_deployment_name = os.environ.get("OPENAI_MODEL_DEPLOYMENT_NAME")
        if model_deployment_name is None:
            raise ValueError("Please set the environment variable 'OPENAI_MODEL_DEPLOYMENT_NAME' to your Azure OpenAI model deployment name.")
        
        # Get temperature from environment variable with default value
        temperature_str = os.environ.get("OPENAI_TEMPERATURE", "0.7") 
        try:
            self.temperature = float(temperature_str)
        except ValueError:
            raise ValueError(f"Invalid OPENAI_TEMPERATURE value: '{temperature_str}'. Must be a number between 0.0 and 2.0.")
        
        # Validate temperature range with warning for high values
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"OPENAI_TEMPERATURE must be between 0.0 and 2.0, got: {self.temperature}")
        elif self.temperature > 1.0:
            print(f"Warning: Temperature {self.temperature} is high and may produce incoherent results. Consider using 0.0-1.0 range.")
        
        self.model_deployment_name = model_deployment_name
        
        self.client = openai.AzureOpenAI(
            api_key=azure_api_key,  
            api_version=api_version,
            azure_endpoint=azure_endpoint,
        )
    
    def _is_o1_model(self, model_name: str) -> bool:
        """Check if the model is an o1 model (o1 models don't support temperature parameter)"""
        return "o1" in model_name.lower()
    
    def _is_gpt41_model(self, model_name: str) -> bool:
        """Check if the model is a GPT-4.1 model (supports higher token limits)"""
        return "4.1" in model_name or "gpt-4.1" in model_name.lower()
    
    def _get_max_output_tokens(self, model_name: str, requested_tokens: int) -> int:
        """Get the appropriate max tokens based on model capabilities."""
        if self._is_o1_model(model_name):
            # o1 models support up to 100,000 tokens
            return min(requested_tokens, 100000)
        elif self._is_gpt41_model(model_name):
            # GPT-4.1 models support up to 32,768 tokens
            return min(requested_tokens, 32768)
        else:
            # GPT-4o and other models typically support 16,384 or less
            return min(requested_tokens, 16384)
    
    def completion(self, messages: List[Dict[str, str]], max_tokens: int = 10000) -> Any:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum tokens to generate (will be capped based on model)
            
        Returns:
            OpenAI completion response object
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        # Validate message format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must be a dict with 'role' and 'content' keys")
        
        # Get appropriate max tokens for the model
        actual_max_tokens = self._get_max_output_tokens(self.model_deployment_name, max_tokens)
        
        # Prepare completion parameters
        completion_params = {
            "model": self.model_deployment_name,
            "messages": messages,
        }
        
        # Handle token limits and temperature based on model type
        if self._is_o1_model(self.model_deployment_name):
            # O1 models use max_completion_tokens and don't support temperature
            completion_params["max_completion_tokens"] = actual_max_tokens
        else:
            # Other models use max_tokens and support temperature
            completion_params["max_tokens"] = actual_max_tokens
            # Only add temperature if it's not 0 (some models are sensitive to temperature=0)
            if self.temperature > 0:
                completion_params["temperature"] = self.temperature
        
        try:
            response = self.client.chat.completions.create(**completion_params)
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate completion: {str(e)}")
    
    def embedding(self, input_text: str, model: str) -> Any:
        """
        Generate embeddings for the input text.
        
        Args:
            input_text: Text to generate embeddings for
            model: Embedding model to use
            
        Returns:
            OpenAI embeddings response object
        """
        if not input_text or not input_text.strip():
            raise ValueError("Input text cannot be empty")
        
        if not model:
            raise ValueError("Model name cannot be empty")
        
        try:
            response = self.client.embeddings.create(
                input=input_text,
                model=model
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")


def main():
    """Example usage and testing."""
    try:
        client_instance = OpenAIClient()
        print("✅ Azure OpenAI client initialized successfully.")
        print(f"📋 Model: {client_instance.model_deployment_name}")                    
        print(f"🤖 Is O1 model: {client_instance._is_o1_model(client_instance.model_deployment_name)}")
        print(f"🔧 Is GPT-4.1 model: {client_instance._is_gpt41_model(client_instance.model_deployment_name)}")
        
         # Only print temperature if it's not an o1 model
        if not client_instance._is_o1_model(client_instance.model_deployment_name):
            print(f"🌡️  Temperature: {client_instance.temperature}")
        
        # Example completion request
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how can you assist me today?"}
        ]
        
        print("\n🚀 Testing completion...")
        response = client_instance.completion(messages, max_tokens=100)
        print(f"📝 Response: {response.choices[0].message.content}")
        print(f"📊 Tokens used: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()