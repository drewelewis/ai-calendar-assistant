"""
Test script to verify OpenTelemetry integration is working correctly
"""

import asyncio
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from telemetry import (
    initialize_telemetry,
    get_telemetry,
    trace_async_method,
    measure_performance,
    TelemetryContext,
    add_span_attributes,
    record_metric,
    log_with_trace
)


@trace_async_method(operation_name="test.operation")
@measure_performance("test_operation")
async def test_operation(duration: float = 1.0):
    """Test operation that demonstrates telemetry features."""
    
    logger = get_telemetry().get_logger() if get_telemetry() else None
    
    if logger:
        logger.info(f"Starting test operation with duration: {duration}s")
    
    # Add custom attributes to the current span
    add_span_attributes(
        test_duration=duration,
        operation_type="telemetry_test",
        test_timestamp=time.time()
    )
    
    # Simulate some work
    await asyncio.sleep(duration)
    
    # Record a custom metric
    record_metric("test_operations_completed", 1, {
        "duration_category": "short" if duration < 2.0 else "long"
    })
    
    if logger:
        logger.info("Test operation completed successfully")
    
    return f"Operation completed in {duration}s"


async def test_error_handling():
    """Test error handling and tracing."""
    
    @trace_async_method(operation_name="test.error_operation")
    async def failing_operation():
        with TelemetryContext(operation="error_test", expected_error=True):
            log_with_trace("warning", "About to trigger a test error")
            raise ValueError("This is a test error for telemetry validation")
    
    try:
        await failing_operation()
    except ValueError as e:
        logger = get_telemetry().get_logger() if get_telemetry() else None
        if logger:
            logger.error(f"Caught expected test error: {e}")


async def test_multiple_spans():
    """Test multiple nested spans."""
    
    tracer = get_telemetry().get_tracer() if get_telemetry() else None
    if not tracer:
        print("No tracer available")
        return
    
    with tracer.start_as_current_span("test.parent_operation") as parent_span:
        parent_span.set_attribute("test.level", "parent")
        
        # Child operation 1
        with tracer.start_as_current_span("test.child_operation_1") as child_span:
            child_span.set_attribute("test.level", "child")
            child_span.set_attribute("test.child_id", "1")
            await asyncio.sleep(0.1)
        
        # Child operation 2
        with tracer.start_as_current_span("test.child_operation_2") as child_span:
            child_span.set_attribute("test.level", "child")
            child_span.set_attribute("test.child_id", "2")
            await asyncio.sleep(0.1)


async def main():
    """Main test function."""
    
    print("🧪 Testing OpenTelemetry Integration")
    print("=" * 50)
    
    # Initialize telemetry
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string or "your-instrumentation-key" in connection_string:
        print("⚠ Warning: Application Insights connection string not properly configured")
        print("Please update APPLICATIONINSIGHTS_CONNECTION_STRING in your .env file")
        print("Continuing with local telemetry configuration...")
    
    telemetry = initialize_telemetry()
    
    if telemetry:
        print("✅ Telemetry initialized successfully")
        logger = telemetry.get_logger()
        logger.info("Starting telemetry test suite")
    else:
        print("❌ Failed to initialize telemetry")
        return
    
    print("\n1. Testing basic traced operation...")
    result = await test_operation(1.5)
    print(f"   Result: {result}")
    
    print("\n2. Testing error handling...")
    await test_error_handling()
    print("   Error handling test completed")
    
    print("\n3. Testing multiple spans...")
    await test_multiple_spans()
    print("   Multiple spans test completed")
    
    print("\n4. Testing custom metrics...")
    for i in range(5):
        record_metric("test_counter", 1, {"iteration": str(i)})
    print("   Custom metrics recorded")
    
    print("\n5. Testing performance measurement...")
    @measure_performance("quick_test")
    async def quick_operation():
        await asyncio.sleep(0.2)
        return "Quick operation done"
    
    result = await quick_operation()
    print(f"   Result: {result}")
    
    print("\n6. Testing structured logging...")
    log_with_trace("info", "Test log message", 
                   test_id="12345", 
                   operation="logging_test",
                   custom_field="test_value")
    print("   Structured log sent")
    
    print("\n✅ All telemetry tests completed!")
    print("\nTo view telemetry data:")
    print("1. Check Azure Portal → Application Insights → Live Metrics")
    print("2. View traces in Application Insights → Transaction search")
    print("3. Query logs in Application Insights → Logs")
    print("\nSample KQL query to find test data:")
    print("traces | where operation_Name startswith 'test.' | order by timestamp desc")
    
    # Give time for telemetry to flush
    print("\n⏳ Waiting 5 seconds for telemetry to flush...")
    await asyncio.sleep(5)
    print("🎉 Test suite complete!")


if __name__ == "__main__":
    asyncio.run(main())
