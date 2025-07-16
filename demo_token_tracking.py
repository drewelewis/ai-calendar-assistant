"""
Example script demonstrating token tracking capabilities
Shows how token usage is tracked in both spans and metrics
"""

import asyncio
import os
from dotenv import load_dotenv

# Import telemetry components
from telemetry import (
    initialize_telemetry,
    get_telemetry, 
    track_openai_tokens,
    TelemetryContext
)

# Import the AI agent
from ai.agent import Agent

load_dotenv(override=True)


@track_openai_tokens(operation_name="example_openai_call")
async def example_openai_call():
    """Example function showing how to use the token tracking decorator."""
    # This would be your actual OpenAI API call
    # The decorator will automatically track tokens, costs, and latency
    pass


async def main():
    """Demonstrate token tracking in action."""
    
    print("🚀 Token Tracking Demo")
    print("=" * 50)
    
    # Initialize telemetry
    telemetry_success = initialize_telemetry(
        service_name="token-tracking-demo",
        service_version="1.0.0"
    )
    
    if not telemetry_success:
        print("❌ Telemetry initialization failed")
        return
    
    print("✅ Telemetry initialized successfully")
    print()
    
    # Create an agent instance (this will automatically track tokens)
    session_id = "demo-session-12345"
    agent = Agent(session_id=session_id)
    
    print(f"📱 Created agent with session ID: {session_id}")
    print()
    
    # Example messages to test token tracking
    test_messages = [
        "Hello! Can you help me schedule a meeting?",
        "What's my calendar looking like for next week?",
        "Can you create a brief summary of my upcoming appointments?"
    ]
    
    print("💬 Testing token tracking with sample messages:")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"Message {i}: {message}")
        
        try:
            # Use telemetry context to add additional metadata
            with TelemetryContext(
                demo_message_number=i,
                message_type="test",
                user_id="demo-user"
            ):
                response = await agent.invoke(message)
                
                print(f"Response: {response[:100]}...")
                print("✅ Token usage tracked automatically")
                print()
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            print()
    
    print("📊 Token tracking summary:")
    print("- Per-request token counts added to spans")
    print("- Aggregated metrics recorded for cost monitoring")
    print("- Latency and error tracking included")
    print("- All data sent to Azure Application Insights")
    print()
    
    # Get telemetry instance to show what metrics are available
    telemetry = get_telemetry()
    if telemetry and telemetry.is_configured:
        print("📈 Available metrics:")
        metrics = telemetry.create_custom_metrics()
        for metric_name in metrics.keys():
            print(f"  - {metric_name}")
    
    print()
    print("🔍 View your telemetry data in Azure Application Insights:")
    print("  - Spans: Search for 'openai' or 'semantic_kernel' operations")
    print("  - Metrics: Look for 'openai_tokens_total' and 'openai_token_cost_total'")
    print("  - Logs: Filter by service name and session ID")


if __name__ == "__main__":
    asyncio.run(main())
