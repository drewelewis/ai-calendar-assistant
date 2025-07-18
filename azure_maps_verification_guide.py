#!/usr/bin/env python3
"""
Azure Maps Key Verification Guide
"""

print("🗺️  Azure Maps Key Verification Steps")
print("=" * 60)

print("\n📊 Current Key Analysis:")
print("   ✅ Key is loading correctly from .env file")
print("   ✅ Key has correct length (84 characters)")  
print("   ❌ Key returns 401 Unauthorized from Azure Maps API")

print("\n🔍 Next Steps - Verify in Azure Portal:")
print("\n1. 🌐 Go to Azure Portal: https://portal.azure.com")

print("\n2. 🔍 Find Your Azure Maps Account:")
print("   → Search for 'Azure Maps' in the top search bar")
print("   → Click on your Azure Maps account")

print("\n3. 🔑 Check Keys and Endpoint:")
print("   → Click 'Keys and Endpoint' in left sidebar")
print("   → Verify the 'Primary Key' matches your .env file")
print("   → Try copying the 'Secondary Key' if primary doesn't work")

print("\n4. 📊 Check Account Status:")
print("   → Go to 'Overview' tab")
print("   → Verify Status is 'Running' or 'Active'")
print("   → Check the Resource Group and Subscription")

print("\n5. 💰 Check Pricing Tier:")
print("   → Go to 'Pricing tier' in left sidebar")
print("   → Ensure it's set to S0 (free) or S1 (paid)")
print("   → Verify the account is not suspended")

print("\n6. 🌐 Check Network Access:")
print("   → Go to 'Networking' (if available)")
print("   → Ensure 'Allow access from all networks' is selected")
print("   → Or add your IP to allowed list")

print("\n7. 📋 Check API Permissions:")
print("   → Go to 'Access control (IAM)'")
print("   → Verify you have 'Reader' or 'Contributor' access")

print("\n🛠️  Troubleshooting Options:")

print("\n   Option A - Generate New Key:")
print("   → In 'Keys and Endpoint', click 'Regenerate key'")
print("   → Copy the new Primary Key")
print("   → Update your .env file with new key")

print("\n   Option B - Create New Azure Maps Account:")
print("   → Create a resource → Search 'Azure Maps'")
print("   → Choose S0 pricing tier (free)")
print("   → Get the subscription key from new account")

print("\n   Option C - Check Different Regions:")
print("   → Some keys are region-specific")
print("   → Try creating Azure Maps in different region")

print("\n📝 Common Issues:")
print("   • Account suspended due to billing issues")
print("   • Key generated for wrong subscription")
print("   • Network/firewall restrictions")
print("   • Account created in preview/beta region")

print("\n🧪 Test Commands:")
print("   After updating the key, run:")
print("   → python quick_test.py")
print("   → python test_azure_maps_local.py")

print("\n💡 Key Format Check:")
import os
from dotenv import load_dotenv
load_dotenv()

key = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY", "")
if key:
    print(f"   Current key: {key[:12]}...{key[-8:]}")
    print(f"   Length: {len(key)} characters")
    
    if len(key) == 64:
        print("   ✅ Standard Azure Maps key length")
    elif len(key) == 84:
        print("   ⚠️  Longer than typical (might be newer format)")
    else:
        print("   ❌ Unusual key length")
else:
    print("   ❌ No key found")

print(f"\n🔗 Useful Links:")
print(f"   • Azure Maps Portal: https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/Microsoft.Maps%2Faccounts")
print(f"   • Azure Maps Docs: https://docs.microsoft.com/en-us/azure/azure-maps/")
print(f"   • Pricing: https://azure.microsoft.com/en-us/pricing/details/azure-maps/")
