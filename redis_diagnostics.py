#!/usr/bin/env python3
"""
Redis Diagnostics Script
This script will help diagnose why Redis cache messages aren't appearing in console.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_redis_configuration():
    """Check Redis configuration and dependencies."""
    print("🔍 Redis Configuration Diagnostics")
    print("=" * 50)
    
    # Check environment variables
    print("1️⃣  Environment Variables:")
    print("-" * 30)
    redis_url = os.environ.get('REDIS_URL', 'NOT SET')
    redis_password = os.environ.get('REDIS_PASSWORD', 'NOT SET')
    redis_cache_enabled = os.environ.get('REDIS_CACHE_ENABLED', 'NOT SET')
    
    print(f"REDIS_URL: {redis_url}")
    print(f"REDIS_PASSWORD: {'***HIDDEN***' if redis_password != 'NOT SET' else 'NOT SET'}")
    print(f"REDIS_CACHE_ENABLED: {redis_cache_enabled}")
    print("")
    
    # Check Redis package availability
    print("2️⃣  Redis Package Availability:")
    print("-" * 30)
    
    try:
        import redis
        print(f"✅ redis package available (version: {redis.__version__})")
        redis_available = True
    except ImportError as e:
        print(f"❌ redis package not available: {e}")
        redis_available = False
    
    try:
        import aioredis
        print(f"✅ aioredis package available (version: {aioredis.__version__})")
        aioredis_available = True
    except ImportError as e:
        print(f"❌ aioredis package not available: {e}")
        aioredis_available = False
    
    print("")
    
    # Check console logging configuration
    print("3️⃣  Console Logging Configuration:")
    print("-" * 30)
    console_enabled = os.environ.get('TELEMETRY_CONSOLE_ENABLED', 'NOT SET')
    console_level = os.environ.get('TELEMETRY_CONSOLE_LEVEL', 'NOT SET')
    telemetry_disabled = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', 'NOT SET')
    
    print(f"TELEMETRY_CONSOLE_ENABLED: {console_enabled}")
    print(f"TELEMETRY_CONSOLE_LEVEL: {console_level}")
    print(f"TELEMETRY_EXPLICITLY_DISABLED: {telemetry_disabled}")
    print("")
    
    # Test Redis connection
    if redis_available and aioredis_available and redis_url != 'NOT SET':
        print("4️⃣  Redis Connection Test:")
        print("-" * 30)
        
        import asyncio
        
        async def test_redis_connection():
            try:
                import aioredis
                # Try to connect
                redis_client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # Test ping
                await redis_client.ping()
                print("✅ Redis connection successful!")
                
                # Close connection
                await redis_client.close()
                
            except Exception as e:
                print(f"❌ Redis connection failed: {e}")
        
        try:
            asyncio.run(test_redis_connection())
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
    else:
        print("4️⃣  Redis Connection Test:")
        print("-" * 30)
        print("❌ Cannot test connection - missing packages or configuration")
    
    print("")
    
    # Check GraphOperations initialization
    print("5️⃣  GraphOperations Redis Status:")
    print("-" * 30)
    
    try:
        # Add the project root to the path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from operations.graph_operations import GraphOperations
        
        # Create instance (this should show initialization messages)
        graph_ops = GraphOperations()
        
        print(f"Cache enabled: {graph_ops.cache_enabled}")
        print(f"Redis URL: {graph_ops.redis_url}")
        print(f"Cache TTL: {graph_ops.cache_ttl}")
        print(f"Redis client: {graph_ops.redis_client}")
        
        # Check if REDIS_AVAILABLE is accessible
        try:
            # Try to import the REDIS_AVAILABLE variable from the module
            import importlib
            graph_module = importlib.import_module('operations.graph_operations')
            redis_available_flag = getattr(graph_module, 'REDIS_AVAILABLE', 'NOT FOUND')
            print(f"REDIS_AVAILABLE flag: {redis_available_flag}")
        except Exception as e:
            print(f"Could not check REDIS_AVAILABLE flag: {e}")
        
    except Exception as e:
        print(f"❌ Error initializing GraphOperations: {e}")
        import traceback
        traceback.print_exc()
    
    print("")
    
    # Recommendations
    print("🔧 Recommendations:")
    print("-" * 30)
    
    if not redis_available or not aioredis_available:
        print("• Install Redis packages: pip install redis aioredis")
    
    if redis_url == 'NOT SET':
        print("• Set REDIS_URL in your .env file")
    
    if redis_cache_enabled.lower() not in ('true', '1', 'yes'):
        print("• Set REDIS_CACHE_ENABLED=true in your .env file")
    
    if console_level != 'DEBUG':
        print("• Set TELEMETRY_CONSOLE_LEVEL=DEBUG to see debug messages")
    
    if telemetry_disabled.lower() in ('true', '1', 'yes'):
        print("• Set TELEMETRY_EXPLICITLY_DISABLED=false to enable telemetry")
    
    print("")

if __name__ == "__main__":
    check_redis_configuration()
