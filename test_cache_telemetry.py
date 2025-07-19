#!/usr/bin/env python3
"""
Redis Cache Telemetry Test Script
This script demonstrates and tests all the telemetry and logging for Redis cache operations.
"""

import asyncio
import os
import sys
import time
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from operations.graph_operations import GraphOperations

async def test_cache_telemetry():
    """Test Redis cache operations with comprehensive telemetry and logging."""
    
    print("🧪 Redis Cache Telemetry Test")
    print("=" * 60)
    
    # Initialize GraphOperations
    graph_ops = GraphOperations()
    
    print(f"📊 Cache Status: {'enabled' if graph_ops.cache_enabled else 'disabled'}")
    print(f"🔗 Redis URL: {graph_ops.redis_url}")
    print(f"⏱️  Default TTL: {graph_ops.cache_ttl}s")
    print("")
    
    if not graph_ops.cache_enabled:
        print("❌ Cache is disabled. Enable it in your .env file to see telemetry.")
        return
    
    try:
        # Test 1: Redis Connection (with telemetry: @trace_async_method("redis_connect"))
        print("1️⃣  Testing Redis Connection...")
        print("-" * 40)
        redis_client = await graph_ops._get_redis_client()
        if redis_client:
            print("✅ Redis connection established")
        else:
            print("❌ Redis connection failed")
            return
        print("")
        
        # Test 2: Cache Miss Scenario (with telemetry: @trace_async_method("cache_get"))
        print("2️⃣  Testing Cache Miss Scenario...")
        print("-" * 40)
        test_key = "graph:test_method:abc123"
        result = await graph_ops._get_from_cache(test_key)
        print(f"Cache result: {result}")
        print("")
        
        # Test 3: Cache Set Operation (with telemetry: @trace_async_method("cache_set"))
        print("3️⃣  Testing Cache Set Operation...")
        print("-" * 40)
        test_data = {
            "users": [
                {"id": "123", "name": "John Doe", "email": "john@company.com"},
                {"id": "456", "name": "Jane Smith", "email": "jane@company.com"}
            ],
            "timestamp": datetime.now().isoformat(),
            "count": 2
        }
        await graph_ops._set_cache(test_key, test_data, 300)
        print("✅ Test data cached")
        print("")
        
        # Test 4: Cache Hit Scenario (with telemetry: @trace_async_method("cache_get"))
        print("4️⃣  Testing Cache Hit Scenario...")
        print("-" * 40)
        cached_result = await graph_ops._get_from_cache(test_key)
        print(f"Cached data retrieved: {len(str(cached_result))} characters")
        print("")
        
        # Test 5: Full Cache Wrapper Test (with telemetry: @trace_async_method("cache_wrapper"))
        print("5️⃣  Testing Full Cache Wrapper...")
        print("-" * 40)
        
        # Mock a Graph API method
        async def mock_graph_method(user_count: int):
            """Mock Graph API call that takes some time."""
            await asyncio.sleep(0.1)  # Simulate API call
            return {
                "users": [{"id": f"user_{i}", "name": f"User {i}"} for i in range(user_count)],
                "total": user_count,
                "timestamp": datetime.now().isoformat()
            }
        
        # First call - should be cache miss and call the API
        print("First call (cache miss):")
        result1 = await graph_ops._cache_wrapper(
            "mock_graph_method", 
            "user_info", 
            mock_graph_method, 
            10
        )
        print(f"Result: {result1['total']} users")
        print("")
        
        # Second call - should be cache hit
        print("Second call (cache hit):")
        result2 = await graph_ops._cache_wrapper(
            "mock_graph_method", 
            "user_info", 
            mock_graph_method, 
            10
        )
        print(f"Result: {result2['total']} users")
        print("")
        
        # Test 6: Cache Statistics
        print("6️⃣  Cache Configuration Summary...")
        print("-" * 40)
        print("TTL Configuration:")
        for cache_type, ttl in graph_ops.cache_ttl_config.items():
            print(f"  • {cache_type}: {ttl}s ({ttl/60:.1f} minutes)")
        print("")
        
        # Test 7: Error Handling
        print("7️⃣  Testing Error Handling...")
        print("-" * 40)
        try:
            # Test with invalid data that might cause serialization issues
            await graph_ops._set_cache("test:invalid", lambda x: x, 60)
        except Exception as e:
            print(f"Expected error handled: {e}")
        print("")
        
        print("🎯 Telemetry Data Generated:")
        print("-" * 40)
        print("In Application Insights, you'll find these operation names:")
        print("  • redis_connect - Redis connection establishment")
        print("  • cache_get - Cache retrieval operations")
        print("  • cache_set - Cache storage operations") 
        print("  • cache_wrapper - Full cache wrapper operations")
        print("  • cache_close - Cache connection cleanup")
        print("")
        print("Search queries for Application Insights:")
        print("  traces | where operation_Name contains 'cache'")
        print("  traces | where operation_Name == 'redis_connect'")
        print("  traces | where cloud_RoleName == 'ai-calendar-assistant'")
        print("")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Test 8: Connection Cleanup (with telemetry: @trace_async_method("cache_close"))
        print("8️⃣  Testing Connection Cleanup...")
        print("-" * 40)
        await graph_ops.close_cache()
        print("✅ Cache cleanup completed")
        print("")

def main():
    """Run the cache telemetry test."""
    print(f"🚀 Starting cache telemetry test at {datetime.now()}")
    print("")
    
    # Check if telemetry is enabled
    telemetry_disabled = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', '').lower() in ('true', '1', 'yes')
    if telemetry_disabled:
        print("⚠️  TELEMETRY IS DISABLED!")
        print("   Set TELEMETRY_EXPLICITLY_DISABLED=false in your .env file")
        print("   to see telemetry data in Application Insights.")
        print("")
    else:
        print("✅ Telemetry is enabled - data will be sent to Application Insights")
        print("")
    
    asyncio.run(test_cache_telemetry())
    
    print("🏁 Cache telemetry test completed!")
    print("")
    print("📈 Check Application Insights in 2-5 minutes for:")
    print("   • Operation traces for cache operations")
    print("   • Performance metrics")
    print("   • Error logs (if any)")
    print("   • Custom dimensions with cache keys and timing")

if __name__ == "__main__":
    main()
