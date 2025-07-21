#!/usr/bin/env python3
"""
Force Redis Connection Test
This script will make Graph API calls that trigger Redis connection attempts so you can see Redis activity in the console.
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_redis_with_graph_calls():
    """Make Graph API calls that will trigger Redis connection attempts."""
    print("🔍 Testing Redis with Graph API Calls")
    print("=" * 50)
    
    print("🔧 Environment Check:")
    redis_url = os.environ.get('REDIS_URL')
    redis_cache_enabled = os.environ.get('REDIS_CACHE_ENABLED')
    print(f"   REDIS_URL: {redis_url}")
    print(f"   REDIS_CACHE_ENABLED: {redis_cache_enabled}")
    print("")
    
    if redis_cache_enabled and redis_cache_enabled.lower() != 'true':
        print("⚠️  Redis caching is disabled. Enable it first!")
        return
    
    try:
        from operations.graph_operations import GraphOperations, REDIS_AVAILABLE
        
        print(f"📦 GraphOperations Status:")
        print(f"   REDIS_AVAILABLE: {REDIS_AVAILABLE}")
        print("")
        
        print("🔄 Initializing GraphOperations (this should show Redis status)...")
        graph_ops = GraphOperations()
        
        print(f"   Cache enabled: {graph_ops.cache_enabled}")
        print(f"   Redis URL: {graph_ops.redis_url}")
        print("")
        
        if not graph_ops.cache_enabled:
            print("❌ Redis caching is not enabled in GraphOperations!")
            print("   This means REDIS_AVAILABLE is False or REDIS_CACHE_ENABLED is not 'true'")
            return
        
        print("🚀 Making Graph API calls that will trigger Redis connection attempts...")
        print("   Watch the console for Redis connection messages!")
        print("")
        
        # Call 1: Get all users (should trigger Redis connection)
        print("📞 Calling get_all_users()...")
        try:
            users = await graph_ops.get_all_users()
            print(f"   ✅ Retrieved {len(users) if users else 0} users")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("")
        
        # Call 2: Get user by ID (should trigger Redis connection if not already connected)
        print("📞 Calling get_user_by_user_id()...")
        try:
            user_id = "12345678-1234-1234-1234-123456789abc"  # Example user ID
            user = await graph_ops.get_user_by_user_id(user_id)
            print(f"   ✅ Retrieved user data")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("")
        
        # Close cache connection
        print("🔒 Closing cache connection...")
        try:
            await graph_ops.close_cache()
            print("   ✅ Cache connection closed")
        except Exception as e:
            print(f"   ⚠️  Error closing cache: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 This script will force Redis connection attempts.")
    print("   Look for messages like:")
    print("   [GraphOps] 🔄 Establishing Redis connection...")
    print("   [GraphOps] 📡 REDIS_CONNECTION_ATTEMPT: ...")
    print("   [GraphOps] ✅ Redis cache connected successfully...")
    print("   OR")
    print("   [GraphOps] 🚨 Redis connection failed after X.XXXs: ...")
    print("")
    
    asyncio.run(test_redis_with_graph_calls())
