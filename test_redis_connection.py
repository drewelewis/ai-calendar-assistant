#!/usr/bin/env python3
"""
Redis Connection Test Script
This script tests your Redis connection with the updated configuration.
"""

import os
import asyncio
from dotenv import load_dotenv

# Clear any existing environment variables first
if 'REDIS_URL' in os.environ:
    del os.environ['REDIS_URL']

# Load environment variables (force reload)
load_dotenv(override=True)

async def test_redis_connection():
    """Test Redis connection using the same configuration as the application."""
    print("🔍 Testing Redis Connection")
    print("=" * 50)
    
    # Check environment variables
    redis_url = os.environ.get('REDIS_URL')
    redis_password = os.environ.get('REDIS_PASSWORD')
    redis_cache_enabled = os.environ.get('REDIS_CACHE_ENABLED', 'true')
    
    print(f"REDIS_URL: {redis_url}")
    print(f"REDIS_PASSWORD: {'***HIDDEN***' if redis_password else 'NOT SET'}")
    print(f"REDIS_CACHE_ENABLED: {redis_cache_enabled}")
    print("")
    
    if not redis_url:
        print("❌ REDIS_URL not set!")
        return
    
    # Test Redis packages availability
    try:
        import redis.asyncio as redis_async
        print("✅ redis.asyncio package available")
        redis_client_class = redis_async.Redis
    except ImportError:
        try:
            import aioredis
            print("✅ aioredis package available")
            redis_client_class = aioredis
        except ImportError:
            print("❌ Neither redis.asyncio nor aioredis packages available")
            return
    
    # Test connection
    print("🔄 Testing Redis connection...")
    try:
        if hasattr(redis_client_class, 'from_url'):
            # redis.asyncio.Redis or newer aioredis
            redis_client = redis_client_class.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True
            )
        else:
            # Fallback
            redis_client = redis_client_class(
                url=redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        
        # Test ping
        await redis_client.ping()
        print("✅ Redis connection successful!")
        
        # Test set/get
        test_key = "test:connection:check"
        test_value = "Hello Redis!"
        
        await redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = await redis_client.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis read/write test successful!")
        else:
            print(f"❌ Redis read/write test failed. Expected: {test_value}, Got: {retrieved_value}")
        
        # Clean up
        await redis_client.delete(test_key)
        await redis_client.close()
        
        print("✅ Redis connection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Try to diagnose common issues
        if "getaddrinfo failed" in str(e):
            print("   This is typically a DNS resolution issue.")
            print("   - Check if the hostname is correct")
            print("   - Verify network connectivity")
            print("   - Try using IP address instead of hostname if available")
        elif "Connection refused" in str(e):
            print("   This suggests the Redis server is not running or not accessible")
            print("   - Check if Redis server is running")
            print("   - Verify port number and firewall settings")
        elif "Authentication" in str(e) or "Auth" in str(e):
            print("   This is an authentication issue")
            print("   - Check if password is correct")
            print("   - Verify the Redis URL format includes password")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())
