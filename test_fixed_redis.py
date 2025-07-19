#!/usr/bin/env python3
"""
Test the fixed Redis import
"""

print("🔍 Testing fixed Redis import...")

try:
    # First test just importing the module
    import operations.graph_operations as graph_ops
    print(f"✅ Module import successful!")
    
    # Check Redis status
    redis_available = getattr(graph_ops, 'REDIS_AVAILABLE', False)
    redis_client_class = getattr(graph_ops, 'redis_client_class', None)
    
    print(f"   REDIS_AVAILABLE: {redis_available}")
    print(f"   redis_client_class: {redis_client_class}")
    
    if redis_available:
        print("🎉 Redis caching is now available!")
        
        # Test GraphOperations class
        try:
            go = graph_ops.GraphOperations()
            print(f"   GraphOperations cache_enabled: {go.cache_enabled}")
        except Exception as go_error:
            print(f"   GraphOperations creation error: {go_error}")
    else:
        print("❌ Redis caching is still disabled")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
