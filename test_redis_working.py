#!/usr/bin/env python3
"""
Test GraphOperations with Redis after package installation
"""
import os
import sys
import asyncio
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Now test the GraphOperations
try:
    print("🔄 Testing GraphOperations Redis integration...")
    
    # Import after packages are installed
    from operations.graph_operations import GraphOperations, REDIS_AVAILABLE
    
    print(f"✅ REDIS_AVAILABLE: {REDIS_AVAILABLE}")
    
    # Create GraphOperations instance
    graph_ops = GraphOperations()
    
    print(f"📊 Cache enabled: {graph_ops.cache_enabled}")
    print(f"🔗 Redis URL: {graph_ops.redis_url}")
    print(f"⏱️  Cache TTL: {graph_ops.cache_ttl}s")
    
    if graph_ops.cache_enabled:
        print("🎉 SUCCESS: Redis caching is now enabled!")
        print("🚀 Next time you run get_all_users, you should see Redis cache messages!")
    else:
        print("❌ Cache is still disabled. Checking why...")
        print(f"   REDIS_AVAILABLE: {REDIS_AVAILABLE}")
        print(f"   REDIS_CACHE_ENABLED env: {os.environ.get('REDIS_CACHE_ENABLED', 'NOT SET')}")
        
        # Try importing Redis directly
        try:
            import redis
            import aioredis
            print("   ✅ Redis packages can be imported directly")
        except ImportError as e:
            print(f"   ❌ Redis packages still can't be imported: {e}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    print(f"🧪 Redis Test completed at {datetime.now()}")
