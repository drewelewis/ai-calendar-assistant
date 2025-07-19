#!/usr/bin/env python3
"""
Test OpenAI and Redis Configuration
Verifies that both OpenAI and Redis configurations are working properly.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def test_configuration():
    """Test configuration values."""
    print("🔍 Configuration Test")
    print("=" * 40)
    
    # Test OpenAI configuration
    openai_endpoint = os.environ.get('OPENAI_ENDPOINT')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    print("1️⃣ OpenAI Configuration:")
    print(f"   OPENAI_ENDPOINT: {openai_endpoint}")
    print(f"   OPENAI_API_KEY: {'***SET***' if openai_api_key else 'NOT SET'}")
    
    if openai_endpoint and openai_endpoint.startswith('https://') and openai_endpoint.endswith('.com/'):
        print("   ✅ OpenAI endpoint format looks correct")
    else:
        print("   ❌ OpenAI endpoint format issue")
    
    # Test Redis configuration
    redis_url = os.environ.get('REDIS_URL')
    redis_cache_enabled = os.environ.get('REDIS_CACHE_ENABLED')
    
    print("\n2️⃣ Redis Configuration:")
    print(f"   REDIS_URL: {redis_url}")
    print(f"   REDIS_CACHE_ENABLED: {redis_cache_enabled}")
    
    if redis_cache_enabled and redis_cache_enabled.lower() == 'true':
        print("   ✅ Redis caching is enabled")
    else:
        print("   ⚠️  Redis caching is disabled")
    
    print("\n3️⃣ GraphOperations Status:")
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from operations.graph_operations import GraphOperations, REDIS_AVAILABLE
        
        print(f"   REDIS_AVAILABLE: {REDIS_AVAILABLE}")
        
        graph_ops = GraphOperations()
        print(f"   Cache enabled: {graph_ops.cache_enabled}")
        print(f"   Redis URL: {graph_ops.redis_url}")
        
        if graph_ops.cache_enabled:
            print("   ✅ GraphOperations initialized with Redis caching enabled")
        else:
            print("   ⚠️  GraphOperations initialized with Redis caching disabled")
        
    except Exception as e:
        print(f"   ❌ Error testing GraphOperations: {e}")

if __name__ == "__main__":
    test_configuration()
