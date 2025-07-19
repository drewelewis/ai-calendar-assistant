#!/usr/bin/env python3
"""
Basic environment check for Azure Maps troubleshooting
"""
import os
import sys

print("🔍 Azure Maps Environment Check")
print("=" * 40)

print("\n📋 Python Environment:")
print(f"   • Python Version: {sys.version}")
print(f"   • Platform: {sys.platform}")

print("\n🔑 Environment Variables:")
azure_maps_key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
azure_maps_client = os.environ.get("AZURE_MAPS_CLIENT_ID")
telemetry_disabled = os.environ.get("TELEMETRY_EXPLICITLY_DISABLED")

print(f"   • AZURE_MAPS_SUBSCRIPTION_KEY: {'✅ Set (' + azure_maps_key[:8] + '...)' if azure_maps_key else '❌ Not set'}")
print(f"   • AZURE_MAPS_CLIENT_ID: {'✅ Set' if azure_maps_client else '❌ Not set'}")
print(f"   • TELEMETRY_EXPLICITLY_DISABLED: {telemetry_disabled}")

print("\n📦 Testing Critical Imports:")

# Test basic imports
try:
    import json
    print("   • json: ✅")
except ImportError as e:
    print(f"   • json: ❌ {e}")

try:
    import asyncio
    print("   • asyncio: ✅")
except ImportError as e:
    print(f"   • asyncio: ❌ {e}")

# Test Azure-related imports
print("\n🔗 Testing Azure Dependencies:")
try:
    import aiohttp
    print("   • aiohttp: ✅")
except ImportError as e:
    print(f"   • aiohttp: ❌ {e}")

try:
    from azure.identity import DefaultAzureCredential
    print("   • azure.identity: ✅")
except ImportError as e:
    print(f"   • azure.identity: ❌ {e}")

try:
    from azure.core.exceptions import ClientAuthenticationError
    print("   • azure.core: ✅")
except ImportError as e:
    print(f"   • azure.core: ❌ {e}")

print("\n💡 Recommendations:")
if azure_maps_key:
    print("   • ✅ You have Azure Maps subscription key configured")
    print("   • 🔧 For local development, subscription key is preferred")
    print("   • 🔧 For Azure deployment, consider managed identity")
else:
    print("   • ❌ No Azure Maps subscription key found")
    print("   • 🔧 Set AZURE_MAPS_SUBSCRIPTION_KEY environment variable")
    print("   • 🔧 Or configure managed identity in Azure")

print("\n🌐 Next Steps for Azure Deployment:")
print("   1. Ensure your Azure resource has managed identity enabled")
print("   2. Assign 'Azure Maps Data Reader' role to the managed identity")
print("   3. Check that your Azure Maps account allows managed identity access")
print("   4. Test the connection from within Azure environment")

print("\n🔧 For Local Development:")
print("   1. Use subscription key from Azure Maps account")
print("   2. Set AZURE_MAPS_SUBSCRIPTION_KEY environment variable")
print("   3. Test locally before deploying to Azure")
