#!/usr/bin/env python3
"""
Debug script for troubleshooting get_all_users returning empty results.
Run this to diagnose Graph API connection and user retrieval issues.
"""

import asyncio
import os
import sys
from operations.graph_operations import GraphOperations

async def debug_users():
    """Debug user retrieval issues."""
    print("🔍 AI Calendar Assistant - User Retrieval Debug")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. 🔧 Checking Environment Variables:")
    tenant_id = os.environ.get("ENTRA_GRAPH_APPLICATION_TENANT_ID")
    client_id = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_ID")
    client_secret = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_SECRET")
    
    print(f"   TENANT_ID: {'✅ Set' if tenant_id else '❌ Missing'}")
    print(f"   CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
    print(f"   CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
    
    if not all([tenant_id, client_id, client_secret]):
        print("\n❌ Missing required environment variables!")
        print("   Please set ENTRA_GRAPH_APPLICATION_TENANT_ID, ENTRA_GRAPH_APPLICATION_CLIENT_ID, and ENTRA_GRAPH_APPLICATION_CLIENT_SECRET")
        return
    
    # Initialize Graph Operations
    print("\n2. 🚀 Initializing Graph Operations:")
    try:
        graph_ops = GraphOperations()
        print("   ✅ Graph Operations initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize Graph Operations: {e}")
        return
    
    # Test Graph API connection
    print("\n3. 🌐 Testing Graph API Connection:")
    debug_result = await graph_ops.debug_graph_connection()
    
    if not debug_result['success']:
        print(f"   ❌ Graph API connection failed: {debug_result['message']}")
        return
    
    # Test get_all_users with different parameters
    print("\n4. 📋 Testing get_all_users:")
    
    test_cases = [
        {"max_results": 5, "exclude_inactive_mailboxes": False, "description": "Small sample, no filtering"},
        {"max_results": 5, "exclude_inactive_mailboxes": True, "description": "Small sample, with filtering"},
        {"max_results": 100, "exclude_inactive_mailboxes": False, "description": "Normal size, no filtering"},
        {"max_results": 100, "exclude_inactive_mailboxes": True, "description": "Normal size, with filtering"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['description']}")
        print(f"   Parameters: max_results={test_case['max_results']}, exclude_inactive_mailboxes={test_case['exclude_inactive_mailboxes']}")
        
        try:
            users = await graph_ops.get_all_users(
                max_results=test_case['max_results'],
                exclude_inactive_mailboxes=test_case['exclude_inactive_mailboxes']
            )
            
            print(f"   Result: {'✅' if users else '❌'} Returned {len(users)} users")
            
            if users:
                print("   Sample users:")
                for j, user in enumerate(users[:3]):  # Show first 3
                    display_name = getattr(user, 'display_name', 'No name')
                    mail = getattr(user, 'mail', 'No mail')
                    print(f"     👤 {j+1}. {display_name} ({mail})")
            else:
                print("   ❌ No users returned - this is the issue!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Test cache status
    print("\n5. 🗂️  Cache Status:")
    print(f"   Cache enabled: {graph_ops.cache_enabled}")
    print(f"   Redis URL: {graph_ops.redis_url}")
    
    if graph_ops.cache_enabled:
        print("   💡 Try disabling cache by setting REDIS_CACHE_ENABLED=false")
    
    # Test without cache wrapper (direct implementation)
    print("\n6. 🔍 Testing Direct Implementation (bypassing cache):")
    try:
        users_direct = await graph_ops._get_all_users_impl(10, False)
        print(f"   Direct call result: {'✅' if users_direct else '❌'} Returned {len(users_direct)} users")
        
        if users_direct:
            print("   ✅ Direct implementation works - issue might be with caching")
        else:
            print("   ❌ Direct implementation also fails - issue is with Graph API call")
            
    except Exception as e:
        print(f"   ❌ Direct implementation error: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    if graph_ops.redis_client:
        await graph_ops.close_cache()
    
    print("\n🎯 Debug Summary:")
    print("   If direct implementation works but get_all_users doesn't:")
    print("   - Try disabling Redis cache: set REDIS_CACHE_ENABLED=false")
    print("   - Check Redis connection and configuration")
    print("\n   If both fail:")
    print("   - Verify Azure app registration permissions")
    print("   - Check if Microsoft Graph API permissions are granted")
    print("   - Ensure admin consent has been provided")

if __name__ == "__main__":
    try:
        asyncio.run(debug_users())
    except KeyboardInterrupt:
        print("\n👋 Debug cancelled by user")
    except Exception as e:
        print(f"\n❌ Debug script failed: {e}")
        import traceback
        traceback.print_exc()
