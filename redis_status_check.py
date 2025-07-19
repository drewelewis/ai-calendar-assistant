#!/usr/bin/env python3
"""
Redis Status Diagnostic
Shows exactly what Redis status looks like when GraphOperations initializes
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_redis_status():
    print("🔍 Redis Status Diagnostic")
    print("=" * 50)
    
    # Check environment variables
    print("1️⃣ Environment Variables:")
    print(f"   REDIS_URL: {os.environ.get('REDIS_URL', 'NOT SET')}")
    print(f"   REDIS_CACHE_ENABLED: {os.environ.get('REDIS_CACHE_ENABLED', 'NOT SET')}")
    print("")
    
    # Import and check Redis availability
    print("2️⃣ Redis Package Check:")
    try:
        from operations.graph_operations import REDIS_AVAILABLE
        print(f"   REDIS_AVAILABLE: {REDIS_AVAILABLE}")
    except Exception as e:
        print(f"   Error importing REDIS_AVAILABLE: {e}")
    print("")
    
    # Initialize GraphOperations to see Redis status
    print("3️⃣ GraphOperations Initialization:")
    print("   This should show Redis status messages...")
    try:
        from operations.graph_operations import GraphOperations
        graph_ops = GraphOperations()
        
        print(f"   Cache enabled: {graph_ops.cache_enabled}")
        print(f"   Redis URL: {graph_ops.redis_url}")
        print(f"   Cache TTL: {graph_ops.cache_ttl}")
        
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_redis_status()
