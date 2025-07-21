#!/usr/bin/env python3
"""
Verify that x-ms-client-id header fix has been applied to Azure Maps operations.
This script inspects the code to confirm the critical 401 error fix is in place.
"""

import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_x_ms_client_id_fix():
    """Verify that the x-ms-client-id header fix is properly implemented."""
    print("🔍 Verifying Azure Maps x-ms-client-id header fix...")
    print("=" * 60)
    
    # Check environment variables
    azure_maps_client_id = os.environ.get("AZURE_MAPS_CLIENT_ID")
    
    print("📋 Environment Variables Check:")
    print(f"   • AZURE_MAPS_CLIENT_ID: {'✅ Set' if azure_maps_client_id else '❌ Not set'}")
    if azure_maps_client_id:
        print(f"     Value: {azure_maps_client_id}")
    print()
    
    # Read Azure Maps operations file
    azure_maps_file = "operations/azure_maps_operations.py"
    
    if not os.path.exists(azure_maps_file):
        print(f"❌ ERROR: {azure_maps_file} not found")
        return
    
    with open(azure_maps_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Code Analysis:")
    
    # Check for x-ms-client-id header usage
    x_ms_client_id_lines = []
    for i, line in enumerate(content.split('\n'), 1):
        if 'x-ms-client-id' in line.lower():
            x_ms_client_id_lines.append((i, line.strip()))
    
    if x_ms_client_id_lines:
        print(f"   ✅ Found {len(x_ms_client_id_lines)} x-ms-client-id header references:")
        for line_num, line in x_ms_client_id_lines:
            print(f"     Line {line_num}: {line[:80]}...")
    else:
        print("   ❌ No x-ms-client-id header references found")
    
    print()
    
    # Check for Authorization header lines that should have x-ms-client-id
    auth_header_lines = []
    for i, line in enumerate(content.split('\n'), 1):
        if 'headers["Authorization"] = f"Bearer' in line:
            auth_header_lines.append((i, line.strip()))
    
    print(f"📊 Authorization Header Analysis:")
    print(f"   • Found {len(auth_header_lines)} Authorization header assignments")
    print(f"   • Found {len(x_ms_client_id_lines)} x-ms-client-id header assignments")
    
    if len(x_ms_client_id_lines) >= len(auth_header_lines):
        print("   ✅ Good: x-ms-client-id headers are present")
    else:
        print("   ⚠️  Warning: May be missing x-ms-client-id headers")
    
    print()
    
    # Check for specific patterns that indicate the fix is applied
    fix_patterns = [
        r'headers\["x-ms-client-id"\]\s*=\s*self\.client_id',
        r'# Add required x-ms-client-id header for Azure Maps managed identity',
        r'Missing AZURE_MAPS_CLIENT_ID for managed identity authentication'
    ]
    
    print("🎯 Fix Pattern Verification:")
    all_patterns_found = True
    
    for i, pattern in enumerate(fix_patterns, 1):
        if re.search(pattern, content, re.IGNORECASE):
            print(f"   ✅ Pattern {i}: Found - {pattern}")
        else:
            print(f"   ❌ Pattern {i}: Missing - {pattern}")
            all_patterns_found = False
    
    print()
    
    # Summary
    print("📋 Fix Verification Summary:")
    if all_patterns_found and x_ms_client_id_lines and azure_maps_client_id:
        print("   ✅ SUCCESS: x-ms-client-id header fix is properly implemented")
        print("   ✅ Environment variable AZURE_MAPS_CLIENT_ID is set")
        print("   ✅ Code patterns match the expected fix")
        print()
        print("🚀 Next Steps:")
        print("   1. Deploy this fix to your Azure Container App")
        print("   2. Restart the container app to load the new code")
        print("   3. Test Azure Maps functionality")
        print("   4. Monitor logs for successful authentication")
    else:
        print("   ❌ INCOMPLETE: Fix may not be fully implemented")
        if not azure_maps_client_id:
            print("   • Set AZURE_MAPS_CLIENT_ID environment variable")
        if not x_ms_client_id_lines:
            print("   • Add x-ms-client-id header to Azure Maps API calls")
        if not all_patterns_found:
            print("   • Review code patterns for complete fix implementation")
    
    print()
    print("💡 Background:")
    print("   The x-ms-client-id header is required for Azure Maps managed identity")
    print("   authentication. Without it, you get 401 Unauthorized errors even")
    print("   with valid Bearer tokens. This fix was identified in commit c8733ba.")

if __name__ == "__main__":
    verify_x_ms_client_id_fix()
