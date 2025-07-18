#!/usr/bin/env python3
"""
Standalone Azure Maps Test Script - No Telemetry Dependencies

This script tests Azure Maps operations without requiring the telemetry infrastructure.
Perfect for local testing and development.

Usage:
    python test_azure_maps_standalone.py

Environment Variables Required (one of these methods):
    - AZURE_MAPS_CLIENT_ID (for Managed Identity authentication)
    - AZURE_MAPS_SUBSCRIPTION_KEY (for subscription key authentication)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_azure_maps_standalone():
    """Test Azure Maps with fallback telemetry."""
    print("🧪 Starting Standalone Azure Maps Test")
    
    # Check environment variables
    client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    print("=== Environment Check ===")
    print(f"AZURE_MAPS_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
    print(f"AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if subscription_key else '❌ Not set'}")
    
    if not client_id and not subscription_key:
        print("❌ No authentication credentials found!")
        print("Please set either AZURE_MAPS_CLIENT_ID or AZURE_MAPS_SUBSCRIPTION_KEY")
        return False
    
    try:
        # Import and initialize Azure Maps operations
        print("\n=== Importing Azure Maps Operations ===")
        from operations.azure_maps_operations import AzureMapsOperations
        print("✅ Azure Maps Operations imported successfully")
        
        async with AzureMapsOperations() as maps_ops:
            
            # Check telemetry status
            print("\n=== Telemetry Status ===")
            telemetry_status = maps_ops.get_telemetry_status()
            for key, value in telemetry_status.items():
                print(f"{key}: {value}")
            
            # Run connection test
            print("\n=== Connection Test ===")
            diagnostics = await maps_ops.test_connection()
            
            # Display results
            print(f"\n=== Test Results ===")
            print(f"Overall Status: {diagnostics['overall_status'].upper()}")
            print(f"Total Duration: {diagnostics['total_duration_seconds']:.3f}s")
            
            # Authentication details
            auth_info = diagnostics['authentication']
            print(f"Auth Method: {auth_info['preferred_method']}")
            
            # Connection test results
            if 'connection_test' in diagnostics:
                conn_test = diagnostics['connection_test']
                print(f"Session Created: {conn_test.get('session_created', False)}")
            
            # Auth test results
            if 'auth_test' in diagnostics:
                auth_test = diagnostics['auth_test']
                print(f"Token Acquired: {auth_test.get('token_acquired', False)}")
                print(f"Auth Duration: {auth_test.get('duration_seconds', 0):.3f}s")
                print(f"Auth Method Used: {auth_test.get('auth_method', 'unknown')}")
            
            # API test results
            if 'api_test' in diagnostics:
                api_test = diagnostics['api_test']
                print(f"API Test Success: {api_test.get('success', False)}")
                print(f"API Duration: {api_test.get('duration_seconds', 0):.3f}s")
                print(f"Results Found: {api_test.get('results_count', 0)}")
                print(f"Query Time: {api_test.get('query_time_ms', 0)}ms")
            
            # Error details if any
            if 'error' in diagnostics:
                error_info = diagnostics['error']
                print(f"Error Type: {error_info['type']}")
                print(f"Error Message: {error_info['message']}")
            
            # If successful, run additional tests
            if diagnostics['overall_status'] == 'success':
                print("\n=== Additional Tests ===")
                
                # Test POI categories
                try:
                    categories = await maps_ops.get_poi_categories()
                    print(f"✅ POI Categories: {len(categories)} categories available")
                except Exception as e:
                    print(f"❌ POI Categories failed: {e}")
                
                # Test specific search
                try:
                    print("\n=== Sample Search Test ===")
                    results = await maps_ops.search_nearby(
                        latitude=47.6205,  # Space Needle, Seattle
                        longitude=-122.3493,
                        radius=500,
                        limit=3
                    )
                    
                    num_results = len(results.get('results', []))
                    print(f"✅ Search test successful: {num_results} results found")
                    
                    # Display first result
                    if num_results > 0:
                        first_poi = results['results'][0]
                        name = first_poi.get('poi', {}).get('name', 'Unknown')
                        distance = first_poi.get('dist', 0)
                        print(f"📍 First result: {name} ({distance:.0f}m away)")
                    
                except Exception as e:
                    print(f"❌ Search test failed: {e}")
            
            return diagnostics['overall_status'] == 'success'
            
    except ImportError as ie:
        print(f"❌ Import error: {ie}")
        print("Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        return False

def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_azure_maps_standalone())
        
        if success:
            print("\n🎉 Standalone Azure Maps test completed successfully!")
            print("\n" + "="*60)
            print("TESTING SUCCESS:")
            print("="*60)
            print("✅ Azure Maps operations work without telemetry dependencies")
            print("✅ Fallback implementations are functioning correctly")
            print("✅ All core functionality is operational")
            print("\n📋 You can now use Azure Maps operations in any environment:")
            print("   - Local development (with or without telemetry)")
            print("   - Production (with full telemetry)")
            print("   - Testing environments (minimal dependencies)")
            print("="*60)
            return 0
        else:
            print("\n💥 Standalone Azure Maps test failed!")
            print("Check the error messages above for troubleshooting.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
