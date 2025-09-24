# Example usage and testing
import os
import asyncio
import json
from ai.multi_agent import MultiAgentOrchestrator
from telemetry.console_output import console_info

chat_session_id = os.getenv("CHAT_SESSION_ID")


async def main():
    """Example usage of Multi-Agent Orchestrator."""
    console_info("🚀 Starting Multi-Agent AI Calendar Assistant", "MultiAgent")
    
    try:
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(session_id=chat_session_id)

        # Example conversations
        test_messages = [
            "Hello! I need help with scheduling a meeting.",
            "Can you find Mary Smith in our directory?", 
            "Where are some good coffee shops near our office?",
            "What's my calendar looking like for tomorrow?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            console_info(f"\n=== Example {i}: {message} ===", "MultiAgent")
            
            response = await orchestrator.process_message(message)
            console_info(f"Response: {response[:200]}{'...' if len(response) > 200 else ''}", "MultiAgent")
        
        # Get agent status
        status = await orchestrator.get_agent_status()
        console_info(f"\nAgent Status: {json.dumps(status, indent=2)}", "MultiAgent")
        
    except Exception as e:
        console_info(f"Multi-agent test failed: {e}", "MultiAgent")
        raise

if __name__ == "__main__":
    asyncio.run(main())