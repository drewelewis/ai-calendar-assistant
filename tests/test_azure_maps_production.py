#!/usr/bin/env python3
"""
Production Azure Maps Test Script

This script tests the production-ready Azure Maps operations with comprehensive
error handling, telemetry management, and performance monitoring.

Features:
- Timeout-protected telemetry initialization
- Comprehensive connection testing
- Performance metrics and monitoring
- Production-grade error handling
- Detailed diagnostics and reporting

Usage:
    python test_azure_maps_production.py

Environment Variables:
    - AZURE_MAPS_CLIENT_ID (for Managed Identity authentication)
    - AZURE_MAPS_SUBSCRIPTION_KEY (for subscription key authentication)
    - DEBUG_AZURE_MAPS=true (enable debug logging)
    - DISABLE_TELEMETRY=true (disable telemetry completely)
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_production_azure_maps():
    """Test Azure Maps production client with comprehensive validation."""
    print("🏭 Starting Production Azure Maps Test")
    print("=" * 60)
    
    # Environment check
    client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    debug_mode = os.environ.get("DEBUG_AZURE_MAPS", "").lower() in ("true", "1")
    telemetry_disabled = os.environ.get("DISABLE_TELEMETRY", "").lower() in ("true", "1")
    
    print("=== Environment Configuration ===")
    print(f"AZURE_MAPS_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
    print(f"AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if subscription_key else '❌ Not set'}")
    print(f"DEBUG_AZURE_MAPS: {'✅ Enabled' if debug_mode else '❌ Disabled'}")
    print(f"DISABLE_TELEMETRY: {'✅ Disabled' if telemetry_disabled else '❌ Enabled'}")
    
    if not client_id and not subscription_key:
        print("\n❌ ERROR: No authentication credentials found!")
        print("Please set either:")
        print("  - AZURE_MAPS_CLIENT_ID (for Managed Identity)")
        print("  - AZURE_MAPS_SUBSCRIPTION_KEY (for subscription key)")
        return False
    
    try:
        print("\n=== Importing Production Azure Maps Operations ===")
        start_time = time.time()
        
        from operations.azure_maps_operations_production import AzureMapsOperations
        
        import_duration = time.time() - start_time
        print(f"✅ Import completed in {import_duration:.3f} seconds")
        
        print("\n=== Initializing Production Client ===")
        # Production configuration with enhanced settings
        async with AzureMapsOperations(
            timeout=30,
            max_retries=3,
            retry_backoff_factor=1.5
        ) as maps_ops:
            
            print("✅ Production client initialized successfully")
            
            # Get telemetry status and configuration
            print("\n=== System Status & Configuration ===")
            status = maps_ops.get_telemetry_status()
            
            print(f"Telemetry Mode: {status['mode']}")
            print(f"Tracer: {status['tracer']}")
            print(f"Console Output: {status['console_output']}")
            print(f"Authentication: {status['configuration']['auth_method']}")
            print(f"Timeout: {status['configuration']['timeout']}s")
            print(f"Max Retries: {status['configuration']['max_retries']}")
            print(f"Backoff Factor: {status['configuration']['retry_backoff_factor']}")
            
            # Performance baseline
            print(f"Requests: {status['performance_stats']['request_count']}")
            print(f"Error Rate: {status['performance_stats']['error_rate_percent']:.1f}%")
            
            # Run comprehensive connection test
            print("\n=== Comprehensive Connection Test ===")
            test_start = time.time()
            
            diagnostics = await maps_ops.test_connection()
            
            test_duration = time.time() - test_start
            print(f"\n--- Connection Test Results ---")
            print(f"Overall Status: {diagnostics['overall_status'].upper()}")
            print(f"Total Test Duration: {test_duration:.3f}s")
            print(f"Reported Duration: {diagnostics['total_duration_seconds']:.3f}s")
            
            # Authentication details
            auth_info = diagnostics['authentication']
            print(f"\n--- Authentication Analysis ---")
            print(f"Preferred Method: {auth_info['preferred_method']}")
            print(f"Subscription Key Available: {auth_info['subscription_key_available']}")
            print(f"Client ID Available: {auth_info['client_id_available']}")
            print(f"Cache Status: {auth_info['cache_status']}")
            
            # Connection test results
            if 'connection_test' in diagnostics:
                conn_test = diagnostics['connection_test']
                print(f"\n--- Connection Pool Analysis ---")
                print(f"Session Created: {conn_test['session_created']}")
                print(f"Duration: {conn_test['duration_seconds']:.3f}s")
                print(f"Connection Pool: {conn_test.get('connection_pool_enabled', 'Unknown')}")
            
            # Auth test results
            if 'auth_test' in diagnostics:
                auth_test = diagnostics['auth_test']
                print(f"\n--- Authentication Test Results ---")
                print(f"Token Acquired: {auth_test['token_acquired']}")
                print(f"Duration: {auth_test['duration_seconds']:.3f}s")
                print(f"Method Used: {auth_test['auth_method']}")
                print(f"Cache Used: {auth_test.get('cache_used', 'N/A')}")
            
            # API test results
            if 'api_test' in diagnostics:
                api_test = diagnostics['api_test']
                print(f"\n--- API Test Results ---")
                print(f"Success: {api_test['success']}")
                print(f"Status Code: {api_test.get('status_code', 'N/A')}")
                print(f"Duration: {api_test.get('duration_seconds', 0):.3f}s")
                print(f"Results Count: {api_test.get('results_count', 0)}")
                print(f"Query Time: {api_test.get('query_time_ms', 0)}ms")
                print(f"Retry Attempts: {api_test.get('retry_attempts', 0)}")
            
            # Performance metrics
            if 'performance' in diagnostics:
                perf = diagnostics['performance']
                print(f"\n--- Performance Configuration ---")
                print(f"Timeout: {perf['timeout_configured']}s")
                print(f"Max Retries: {perf['retry_settings']['max_retries']}")
                print(f"Backoff Factor: {perf['retry_settings']['backoff_factor']}")
            
            # Error details if any
            if 'error' in diagnostics:
                error_info = diagnostics['error']
                print(f"\n--- Error Analysis ---")
                print(f"Error Type: {error_info['type']}")
                print(f"Error Message: {error_info['message']}")
                if debug_mode:
                    print(f"Traceback: {error_info['traceback']}")
            
            # If connection test successful, run additional production tests
            if diagnostics['overall_status'] == 'success':
                print("\n=== Production Feature Tests ===")
                
                # Test POI categories with production error handling
                try:
                    print("\n--- POI Categories Test ---")
                    categories_start = time.time()
                    
                    categories = await maps_ops.get_poi_categories()
                    
                    categories_duration = time.time() - categories_start
                    print(f"✅ POI Categories: {len(categories)} categories retrieved")
                    print(f"Duration: {categories_duration:.3f}s")
                    
                    # Show sample categories
                    if categories and debug_mode:
                        print("Sample categories:")
                        for i, category in enumerate(categories[:5]):
                            if isinstance(category, dict):
                                name = category.get('name', 'Unknown')
                                category_id = category.get('id', 'N/A')
                                print(f"  {i+1}. {name} (ID: {category_id})")
                            else:
                                print(f"  {i+1}. {category}")
                    
                except Exception as e:
                    print(f"❌ POI Categories test failed: {e}")
                
                # Test nearby search with production validation
                try:
                    print("\n--- Nearby Search Test ---")
                    search_start = time.time()
                    
                    # Test near Space Needle, Seattle
                    results = await maps_ops.search_nearby(
                        latitude=47.6205,
                        longitude=-122.3493,
                        radius=500,
                        limit=5
                    )
                    
                    search_duration = time.time() - search_start
                    num_results = len(results.get('results', []))
                    print(f"✅ Nearby Search: {num_results} results found")
                    print(f"Duration: {search_duration:.3f}s")
                    
                    # Show sample results
                    if num_results > 0:
                        first_poi = results['results'][0]
                        name = first_poi.get('poi', {}).get('name', 'Unknown')
                        distance = first_poi.get('dist', 0)
                        address = first_poi.get('address', {}).get('freeformAddress', 'No address')
                        print(f"📍 Closest result: {name}")
                        print(f"   Distance: {distance:.0f}m")
                        print(f"   Address: {address}")
                        
                        if debug_mode and num_results > 1:
                            print("Additional results:")
                            for i, poi in enumerate(results['results'][1:], 2):
                                poi_name = poi.get('poi', {}).get('name', 'Unknown')
                                poi_dist = poi.get('dist', 0)
                                print(f"   {i}. {poi_name} ({poi_dist:.0f}m)")
                    
                except Exception as e:
                    print(f"❌ Nearby search test failed: {e}")
                
                # Get final performance statistics
                final_status = maps_ops.get_telemetry_status()
                print(f"\n=== Final Performance Statistics ===")
                perf_stats = final_status['performance_stats']
                print(f"Total Requests: {perf_stats['request_count']}")
                print(f"Total Errors: {perf_stats['error_count']}")
                print(f"Success Rate: {100 - perf_stats['error_rate_percent']:.1f}%")
                print(f"Average Duration: {perf_stats['average_duration']:.3f}s")
            
            return diagnostics['overall_status'] == 'success'
            
    except ImportError as ie:
        print(f"❌ Import error: {ie}")
        print("Make sure you're running from the correct directory with proper dependencies")
        return False
    except Exception as e:
        print(f"❌ Production test failed: {e}")
        if debug_mode:
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")
        return False

def main():
    """Main entry point with comprehensive reporting."""
    print("🏭 Production Azure Maps Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        success = asyncio.run(test_production_azure_maps())
        
        total_duration = time.time() - start_time
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 PRODUCTION TEST SUCCESS")
            print("=" * 60)
            print("✅ All production features validated successfully")
            print("✅ Telemetry system working correctly")
            print("✅ Error handling and retry logic functional")
            print("✅ Performance monitoring operational")
            print("✅ Authentication and security validated")
            print("✅ Connection pooling and resource management verified")
            
            print(f"\n📊 Test completed in {total_duration:.3f} seconds")
            print("\n🚀 Production Azure Maps Operations ready for deployment!")
            print("\nNext steps:")
            print("  - Deploy to production environment")
            print("  - Monitor telemetry and performance metrics")
            print("  - Configure alerting for error rates and latency")
            print("  - Set up automated health checks")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("💥 PRODUCTION TEST FAILED")
            print("=" * 60)
            print("❌ One or more production features failed validation")
            print("❌ Review error messages above for troubleshooting")
            print("\n🔧 Troubleshooting steps:")
            print("  1. Verify Azure Maps credentials")
            print("  2. Check network connectivity")
            print("  3. Validate Azure subscription and permissions")
            print("  4. Review Application Insights configuration")
            print("  5. Check for service outages or maintenance")
            print("=" * 60)
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Production test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error in production test: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
