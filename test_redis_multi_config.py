#!/usr/bin/env python3
"""
Redis Connection Multi-Test Script
This script tests multiple Redis connection configurations to find the working one.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

async def test_redis_configurations():
    """Test multiple Redis configurations to find the working one."""
    print("🔍 Testing Multiple Redis Configurations")
    print("=" * 60)
    
    base_password = os.environ.get('REDIS_PASSWORD', '')
    hostname = "managed-managed-redis.eastus2.redis.azure.net"
    
    # Different configurations to test
    configurations = [
        # Format: (description, redis_url)
        ("Standard TLS (6380)", f"rediss://:{base_password}@{hostname}:6380"),
        ("Enterprise TLS (10000)", f"rediss://:{base_password}@{hostname}:10000"),
        ("Standard non-TLS (6379)", f"redis://:{base_password}@{hostname}:6379"),
        ("Standard TLS no password", f"rediss://{hostname}:6380"),
        ("Enterprise TLS no password", f"rediss://{hostname}:10000"),
    ]
    
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
    
    successful_configs = []
    
    for description, redis_url in configurations:
        print(f"\n🔄 Testing: {description}")
        print(f"   URL: {redis_url[:50]}...")
        
        try:
            if hasattr(redis_client_class, 'from_url'):
                redis_client = redis_client_class.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
            else:
                redis_client = redis_client_class(
                    url=redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            
            # Test ping
            await redis_client.ping()
            print(f"   ✅ Connection successful!")
            successful_configs.append((description, redis_url))
            
            # Clean up
            await redis_client.close()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n{'='*60}")
    print("📊 RESULTS SUMMARY")
    print(f"{'='*60}")
    
    if successful_configs:
        print(f"✅ Found {len(successful_configs)} working configuration(s):")
        for desc, url in successful_configs:
            print(f"   • {desc}: {url}")
        
        print(f"\n🔧 RECOMMENDED .env SETTING:")
        best_config = successful_configs[0]  # Use the first working one
        print(f"REDIS_URL={best_config[1]}")
        
    else:
        print("❌ No working configurations found.")
        print("\n🔧 Troubleshooting suggestions:")
        print("   1. Verify the Redis instance is running")
        print("   2. Check firewall/network security group settings")
        print("   3. Confirm the hostname and credentials are correct")
        print("   4. Try connecting from Azure Cloud Shell or a VM in the same region")

if __name__ == "__main__":
    asyncio.run(test_redis_configurations())
