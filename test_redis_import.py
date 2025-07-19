#!/usr/bin/env python3
"""
Test script to isolate Redis import issues
"""

print("🔍 Testing Redis import conflict...")

# Test 1: Import aioredis alone
try:
    import aioredis
    print("✅ Step 1: aioredis imports successfully")
except Exception as e:
    print(f"❌ Step 1: aioredis import failed: {e}")
    exit(1)

# Test 2: Import concurrent.futures after aioredis
try:
    import concurrent.futures
    print("✅ Step 2: concurrent.futures imports successfully after aioredis")
except Exception as e:
    print(f"❌ Step 2: concurrent.futures import failed: {e}")
    exit(1)

# Test 3: Check for TimeoutError conflicts
try:
    timeout_classes = []
    
    if hasattr(aioredis, 'TimeoutError'):
        timeout_classes.append(f"aioredis.TimeoutError: {aioredis.TimeoutError}")
    
    if hasattr(concurrent.futures, 'TimeoutError'):
        timeout_classes.append(f"concurrent.futures.TimeoutError: {concurrent.futures.TimeoutError}")
    
    # Check built-in TimeoutError
    try:
        import builtins
        if hasattr(builtins, 'TimeoutError'):
            timeout_classes.append(f"builtins.TimeoutError: {builtins.TimeoutError}")
    except:
        pass
    
    # Check asyncio TimeoutError
    try:
        import asyncio
        if hasattr(asyncio, 'TimeoutError'):
            timeout_classes.append(f"asyncio.TimeoutError: {asyncio.TimeoutError}")
    except:
        pass
    
    print("🔍 TimeoutError classes found:")
    for tc in timeout_classes:
        print(f"   {tc}")
    
    print("✅ Step 3: TimeoutError analysis completed")
    
except Exception as e:
    print(f"❌ Step 3: TimeoutError analysis failed: {e}")

# Test 4: Try to reproduce the exact import sequence from graph_operations.py
try:
    print("🔍 Step 4: Testing exact import sequence...")
    
    # Simulate the same import order as in graph_operations.py
    import os
    from datetime import datetime
    import traceback
    import asyncio
    import hashlib
    import json
    from typing import List, Dict, Optional, Any
    
    # Now try to import aioredis (this is where the conflict occurs)
    import aioredis as test_aioredis
    print("✅ Step 4: Exact import sequence works!")
    
except Exception as e:
    print(f"❌ Step 4: Exact import sequence failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error details: {e}")

print("🏁 Redis import test completed!")
