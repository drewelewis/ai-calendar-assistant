"""
Demo script for console output telemetry
Shows different types of telemetry events being printed to the console
"""

import os
import asyncio
import time
from datetime import datetime

# Set demo configuration for maximum visibility
os.environ['TELEMETRY_CONSOLE_ENABLED'] = 'true'
os.environ['TELEMETRY_CONSOLE_LEVEL'] = 'DEBUG'
os.environ['TELEMETRY_CONSOLE_COLORS'] = 'true'
os.environ['TELEMETRY_CONSOLE_TIMESTAMP'] = 'true'
os.environ['TELEMETRY_CONSOLE_MODULE'] = 'true'

from telemetry.console_output import (
    console_info, console_debug, console_warning, console_error,
    console_telemetry_event, console_span_start, console_span_end,
    console_token_usage, get_telemetry_console
)


def demonstrate_basic_logging():
    """Demonstrate basic console logging at different levels"""
    print("\n" + "="*60)
    print("🔸 DEMO: Basic Console Logging Levels")
    print("="*60)
    
    console_error("Database connection failed", "demo")
    console_warning("High memory usage detected", "demo")
    console_info("Application started successfully", "demo")
    console_debug("Loading configuration from environment", "demo")


def demonstrate_telemetry_events():
    """Demonstrate structured telemetry events"""
    print("\n" + "="*60)
    print("🔸 DEMO: Structured Telemetry Events")
    print("="*60)
    
    # Chat request event
    console_telemetry_event("chat_request", {
        "session_id": "demo-session-123",
        "message_length": 45,
        "has_cosmosdb": True,
        "user_type": "authenticated"
    }, "agent")
    
    # Database operation event
    console_telemetry_event("cosmosdb_op", {
        "operation": "save_chat_history",
        "collection": "chat_sessions",
        "document_count": 1,
        "duration_ms": 23.4
    }, "storage")
    
    # Error event
    console_telemetry_event("error", {
        "operation": "graph_api_call",
        "error_type": "AuthenticationError",
        "retry_count": 2
    }, "graph")


def demonstrate_span_events():
    """Demonstrate span start/end events"""
    print("\n" + "="*60)
    print("🔸 DEMO: Span Events (Function Tracing)")
    print("="*60)
    
    # Simulate a function execution with span tracking
    span_name = "demo.process_user_request"
    
    console_span_start(span_name, {
        "user_id": "demo-user",
        "request_type": "calendar_query"
    })
    
    # Simulate some work
    time.sleep(0.1)
    
    console_span_end(span_name, 127.5, "OK", {
        "items_processed": 15,
        "cache_hit": True
    })
    
    # Simulate an error case
    error_span = "demo.failing_operation"
    console_span_start(error_span)
    time.sleep(0.05)
    console_span_end(error_span, 52.3, "ERROR", {
        "error": "TimeoutError"
    })


def demonstrate_token_tracking():
    """Demonstrate token usage tracking"""
    print("\n" + "="*60)
    print("🔸 DEMO: Token Usage Tracking")
    print("="*60)
    
    # Simulate different OpenAI API calls
    console_token_usage(
        model="gpt-4o",
        input_tokens=245,
        output_tokens=89,
        total_cost=0.0053,
        operation="chat_completion"
    )
    
    console_token_usage(
        model="gpt-4o-mini",
        input_tokens=156,
        output_tokens=42,
        total_cost=0.0008,
        operation="summarization"
    )
    
    console_token_usage(
        model="text-embedding-3-small",
        input_tokens=89,
        output_tokens=0,
        total_cost=0.0001,
        operation="embedding"
    )


def demonstrate_configuration():
    """Show current configuration"""
    print("\n" + "="*60)
    print("🔸 DEMO: Current Console Configuration")
    print("="*60)
    
    console = get_telemetry_console()
    
    config_info = {
        "enabled": console.enabled,
        "level": console.level.name,
        "colors": console.use_colors,
        "timestamp": console.include_timestamp,
        "module": console.include_module
    }
    
    for key, value in config_info.items():
        console_info(f"Configuration: {key} = {value}", "config")


async def demonstrate_async_operations():
    """Demonstrate console output with async operations"""
    print("\n" + "="*60)
    print("🔸 DEMO: Async Operations")
    print("="*60)
    
    console_info("Starting async operation batch", "async_demo")
    
    # Simulate multiple concurrent operations
    async def simulate_api_call(call_id: int, duration: float):
        span_name = f"async_operation_{call_id}"
        console_span_start(span_name, {"call_id": call_id})
        
        await asyncio.sleep(duration)
        
        console_span_end(span_name, duration * 1000, "OK")
        
        # Simulate token usage for some calls
        if call_id % 2 == 0:
            console_token_usage(
                model="gpt-4o",
                input_tokens=100 + call_id * 10,
                output_tokens=50 + call_id * 5,
                total_cost=0.001 + call_id * 0.0001,
                operation=f"async_call_{call_id}"
            )
    
    # Run multiple operations concurrently
    tasks = [
        simulate_api_call(i, 0.05 + i * 0.01) 
        for i in range(1, 4)
    ]
    
    await asyncio.gather(*tasks)
    console_info("All async operations completed", "async_demo")


def demonstrate_different_levels():
    """Show how different console levels filter output"""
    print("\n" + "="*60)
    print("🔸 DEMO: Console Level Filtering")
    print("="*60)
    
    console = get_telemetry_console()
    original_level = console.level
    
    from telemetry.console_output import ConsoleLevel
    
    for level in [ConsoleLevel.ERROR, ConsoleLevel.WARNING, ConsoleLevel.INFO, ConsoleLevel.DEBUG]:
        console.level = level
        console_info(f"--- Console Level: {level.name} ---", "level_demo")
        
        console_error("This is an ERROR message", "level_demo")
        console_warning("This is a WARNING message", "level_demo")
        console_info("This is an INFO message", "level_demo")
        console_debug("This is a DEBUG message", "level_demo")
        
        print()  # Add spacing
    
    # Restore original level
    console.level = original_level


async def main():
    """Run all demonstrations"""
    print("🚀 Console Output Telemetry Demo")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    demonstrate_configuration()
    demonstrate_basic_logging()
    demonstrate_telemetry_events()
    demonstrate_span_events()
    demonstrate_token_tracking()
    await demonstrate_async_operations()
    demonstrate_different_levels()
    
    print("\n" + "="*60)
    print("✅ Demo completed! Check the output above to see different")
    print("   telemetry events being printed to the console.")
    print("\n💡 To configure console output in your app, set these")
    print("   environment variables:")
    print("   - TELEMETRY_CONSOLE_ENABLED=true/false")
    print("   - TELEMETRY_CONSOLE_LEVEL=ERROR/WARNING/INFO/DEBUG/TRACE")
    print("   - TELEMETRY_CONSOLE_COLORS=true/false")
    print("   - TELEMETRY_CONSOLE_TIMESTAMP=true/false")
    print("   - TELEMETRY_CONSOLE_MODULE=true/false")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
