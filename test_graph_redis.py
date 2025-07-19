#!/usr/bin/env python3
"""
Test Redis with Graph API Call
This script will make a Graph API call that triggers Redis caching, so you can see Redis activity in the console.
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_graph_api_with_redis():
    """Test Graph API call that will trigger Redis caching attempts."""
    print("🔍 Testing Graph API with Redis Caching")
    print("=" * 50)
    
    try:
        from operations.graph_operations import GraphOperations
        
        # Create GraphOperations instance
        graph_ops = GraphOperations()
        
        print(f"✅ GraphOperations initialized")
        print(f"   Cache enabled: {graph_ops.cache_enabled}")
        print(f"   Redis URL: {graph_ops.redis_url}")
        print(f"   Cache TTL: {graph_ops.cache_ttl}")
        print("")
        
        # This should trigger Redis connection attempts
        print("🔄 Making Graph API call that will use caching...")
        print("   This should show Redis connection messages in the console...")
        
        # Make a call that uses caching
        try:
            users = await graph_ops.get_all_users()
            print(f"✅ Graph API call successful! Retrieved {len(users) if users else 0} users")
        except Exception as e:
            print(f"❌ Graph API call failed: {e}")
        
        # Try to close cache connection
        try:
            await graph_ops.close_cache()
            print("✅ Cache connection closed")
        except Exception as e:
            print(f"⚠️  Error closing cache: {e}")
            
    except Exception as e:
        print(f"❌ Error initializing GraphOperations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graph_api_with_redis())
