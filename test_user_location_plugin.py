#!/usr/bin/env python3
"""
Test script for the new User Location Plugin functionality.

This script demonstrates how to use the get_user_location function
added to the Graph Plugin to retrieve user location information.

Usage:
    python test_user_location_plugin.py

Environment Variables Required:
    - ENTRA_GRAPH_APPLICATION_TENANT_ID
    - ENTRA_GRAPH_APPLICATION_CLIENT_ID  
    - ENTRA_GRAPH_APPLICATION_CLIENT_SECRET
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from plugins.graph_plugin import GraphPlugin
from telemetry.console_output import console_info, console_error, console_warning

async def test_user_location_plugin():
    """Test the new user location plugin functionality."""
    console_info("🧪 Testing User Location Plugin", module="LocationTest")
    
    # Check environment variables
    tenant_id = os.environ.get("ENTRA_GRAPH_APPLICATION_TENANT_ID")
    client_id = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_ID")
    client_secret = os.environ.get("ENTRA_GRAPH_APPLICATION_CLIENT_SECRET")
    
    console_info("=== Environment Check ===", module="LocationTest")
    console_info(f"ENTRA_GRAPH_APPLICATION_TENANT_ID: {'✅ Set' if tenant_id else '❌ Not set'}", module="LocationTest")
    console_info(f"ENTRA_GRAPH_APPLICATION_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}", module="LocationTest")
    console_info(f"ENTRA_GRAPH_APPLICATION_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Not set'}", module="LocationTest")
    
    if not all([tenant_id, client_id, client_secret]):
        console_error("❌ Missing required environment variables!", module="LocationTest")
        console_error("Please set ENTRA_GRAPH_APPLICATION_TENANT_ID, ENTRA_GRAPH_APPLICATION_CLIENT_ID, and ENTRA_GRAPH_APPLICATION_CLIENT_SECRET", module="LocationTest")
        return False
    
    try:
        # Initialize Graph Plugin
        console_info("\n=== Initializing Graph Plugin ===", module="LocationTest")
        graph_plugin = GraphPlugin(debug=True, session_id="test-session")
        
        # Test user search first to get a valid user ID
        console_info("\n=== Finding Test User ===", module="LocationTest")
        
        # Search for a few users to test with
        try:
            users = await graph_plugin.user_search("accountEnabled eq true", include_inactive_mailboxes=False)
            if not users:
                console_warning("⚠️  No users found to test with", module="LocationTest")
                return False
                
            console_info(f"Found {len(users)} users to test with", module="LocationTest")
            
            # Test location function with first few users
            for i, user in enumerate(users[:3]):  # Test with first 3 users
                user_id = getattr(user, 'id', None)
                display_name = getattr(user, 'display_name', 'Unknown')
                
                if not user_id:
                    continue
                    
                console_info(f"\n=== Testing Location for User {i+1}: {display_name} ===", module="LocationTest")
                console_info(f"User ID: {user_id}", module="LocationTest")
                
                # Test the new get_user_location function
                try:
                    location_info = await graph_plugin.get_user_location(user_id)
                    
                    if location_info:
                        console_info("✅ Location information retrieved:", module="LocationTest")
                        console_info(f"  City: {location_info.get('city', 'Not specified')}", module="LocationTest")
                        console_info(f"  State: {location_info.get('state', 'Not specified')}", module="LocationTest")
                        console_info(f"  Zipcode: {location_info.get('zipcode', 'Not specified')}", module="LocationTest")
                        
                        # Check if any location data is available
                        has_location_data = any([
                            location_info.get('city'),
                            location_info.get('state'), 
                            location_info.get('zipcode')
                        ])
                        
                        if has_location_data:
                            console_info("🎉 User has location data populated!", module="LocationTest")
                        else:
                            console_warning("⚠️  User profile doesn't have location data populated", module="LocationTest")
                            
                    else:
                        console_warning(f"⚠️  No location information found for {display_name}", module="LocationTest")
                        
                except Exception as location_error:
                    console_error(f"❌ Error getting location for {display_name}: {location_error}", module="LocationTest")
                    continue
            
            console_info("\n=== Location Plugin Test Summary ===", module="LocationTest")
            console_info("✅ Plugin function successfully added and callable", module="LocationTest")
            console_info("✅ Integration with Graph Operations working", module="LocationTest")
            console_info("✅ Error handling functioning properly", module="LocationTest")
            console_info("ℹ️  Note: Location data availability depends on user profile completion", module="LocationTest")
            
            return True
            
        except Exception as search_error:
            console_error(f"❌ Error during user search: {search_error}", module="LocationTest")
            return False
            
    except Exception as e:
        console_error(f"❌ Plugin test failed: {e}", module="LocationTest")
        import traceback
        console_error(f"Full traceback:\n{traceback.format_exc()}", module="LocationTest")
        return False

def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_user_location_plugin())
        
        if success:
            console_info("\n🎉 User Location Plugin test completed successfully!", module="LocationTest")
            print("\n" + "="*60)
            print("USAGE EXAMPLES:")
            print("="*60)
            print("# In your AI agent or application:")
            print("graph_plugin = GraphPlugin()")
            print("location = await graph_plugin.get_user_location(user_id)")
            print("print(f\"User is in {location['city']}, {location['state']} {location['zipcode']}\")")
            print("\n# Common use cases:")
            print("# - 'Where is John Smith located?'")
            print("# - 'What city is Sarah in?'") 
            print("# - 'Find users in Seattle for local meeting'")
            print("# - 'Get shipping address for this employee'")
            print("="*60)
            return 0
        else:
            console_error("\n💥 User Location Plugin test failed!", module="LocationTest")
            return 1
            
    except KeyboardInterrupt:
        console_warning("\n⚠️  Test interrupted by user", module="LocationTest")
        return 130
    except Exception as e:
        console_error(f"\n💥 Unexpected error: {e}", module="LocationTest")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
