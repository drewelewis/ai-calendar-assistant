#!/usr/bin/env python3
"""
Azure Maps Connection Diagnostics Test Script

This script tests the enhanced Azure Maps operations with detailed telemetry and console output.
Run this script to diagnose connection issues with Azure Maps Service.

Usage:
    python test_azure_maps_diagnostics.py

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

from operations.azure_maps_operations import AzureMapsOperations
from telemetry.console_output import console_info, console_error, console_warning

async def test_azure_maps_diagnostics():
    """Test Azure Maps with enhanced diagnostics."""
    console_info("🧪 Starting Azure Maps Diagnostics Test", module="DiagnosticsTest")
    
    # Check environment variables
    client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    subscription_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
    
    console_info("=== Environment Check ===", module="DiagnosticsTest")
    console_info(f"AZURE_MAPS_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}", module="DiagnosticsTest")
    console_info(f"AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set' if subscription_key else '❌ Not set'}", module="DiagnosticsTest")
    
    if not client_id and not subscription_key:
        console_error("❌ No authentication credentials found!", module="DiagnosticsTest")
        console_error("Please set either AZURE_MAPS_CLIENT_ID or AZURE_MAPS_SUBSCRIPTION_KEY", module="DiagnosticsTest")
        return False
    
    try:
        # Initialize Azure Maps operations
        console_info("\n=== Initializing Azure Maps Operations ===", module="DiagnosticsTest")
        async with AzureMapsOperations() as maps_ops:
            
            # Run comprehensive connection test
            console_info("\n=== Running Connection Diagnostics ===", module="DiagnosticsTest")
            diagnostics = await maps_ops.test_connection()
            
            # Display results
            console_info("\n=== Diagnostics Results ===", module="DiagnosticsTest")
            console_info(f"Overall Status: {diagnostics['overall_status'].upper()}", module="DiagnosticsTest")
            console_info(f"Total Duration: {diagnostics['total_duration_seconds']:.3f}s", module="DiagnosticsTest")
            
            # Authentication details
            auth_info = diagnostics['authentication']
            console_info(f"Auth Method: {auth_info['preferred_method']}", module="DiagnosticsTest")
            console_info(f"Has Client ID: {auth_info['has_client_id']}", module="DiagnosticsTest")
            console_info(f"Has Subscription Key: {auth_info['has_subscription_key']}", module="DiagnosticsTest")
            
            # Connection test results
            if 'connection_test' in diagnostics:
                conn_test = diagnostics['connection_test']
                console_info(f"Session Created: {conn_test.get('session_created', False)}", module="DiagnosticsTest")
            
            # Auth test results
            if 'auth_test' in diagnostics:
                auth_test = diagnostics['auth_test']
                console_info(f"Token Acquired: {auth_test.get('token_acquired', False)}", module="DiagnosticsTest")
                console_info(f"Auth Duration: {auth_test.get('duration_seconds', 0):.3f}s", module="DiagnosticsTest")
                console_info(f"Auth Method Used: {auth_test.get('auth_method', 'unknown')}", module="DiagnosticsTest")
            
            # API test results
            if 'api_test' in diagnostics:
                api_test = diagnostics['api_test']
                console_info(f"API Test Success: {api_test.get('success', False)}", module="DiagnosticsTest")
                console_info(f"API Duration: {api_test.get('duration_seconds', 0):.3f}s", module="DiagnosticsTest")
                console_info(f"Results Found: {api_test.get('results_count', 0)}", module="DiagnosticsTest")
                console_info(f"Query Time: {api_test.get('query_time_ms', 0)}ms", module="DiagnosticsTest")
            
            # Error details if any
            if 'error' in diagnostics:
                error_info = diagnostics['error']
                console_error(f"Error Type: {error_info['type']}", module="DiagnosticsTest")
                console_error(f"Error Message: {error_info['message']}", module="DiagnosticsTest")
            
            # If successful, run a simple search test
            if diagnostics['overall_status'] == 'success':
                console_info("\n=== Running Sample Search ===", module="DiagnosticsTest")
                try:
                    # Search for POIs near a well-known location (Space Needle, Seattle)
                    results = await maps_ops.search_nearby(
                        latitude=47.6205,
                        longitude=-122.3493,
                        radius=500,
                        limit=3
                    )
                    
                    num_results = len(results.get('results', []))
                    console_info(f"✅ Sample search successful: {num_results} results", module="DiagnosticsTest")
                    
                    # Display first result
                    if num_results > 0:
                        first_poi = results['results'][0]
                        name = first_poi.get('poi', {}).get('name', 'Unknown')
                        distance = first_poi.get('dist', 0)
                        console_info(f"First result: {name} ({distance:.0f}m away)", module="DiagnosticsTest")
                    
                except Exception as e:
                    console_error(f"❌ Sample search failed: {e}", module="DiagnosticsTest")
            
            return diagnostics['overall_status'] == 'success'
            
    except Exception as e:
        console_error(f"❌ Diagnostics test failed: {e}", module="DiagnosticsTest")
        import traceback
        console_error(f"Full traceback:\n{traceback.format_exc()}", module="DiagnosticsTest")
        return False

def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_azure_maps_diagnostics())
        
        if success:
            console_info("\n🎉 Azure Maps diagnostics completed successfully!", module="DiagnosticsTest")
            return 0
        else:
            console_error("\n💥 Azure Maps diagnostics failed!", module="DiagnosticsTest")
            return 1
            
    except KeyboardInterrupt:
        console_warning("\n⚠️  Test interrupted by user", module="DiagnosticsTest")
        return 130
    except Exception as e:
        console_error(f"\n💥 Unexpected error: {e}", module="DiagnosticsTest")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
