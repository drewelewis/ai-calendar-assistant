#!/usr/bin/env python3
"""
Azure Maps Account Setup Guide
"""

print("🗺️  Azure Maps Setup Guide")
print("=" * 50)

print("\n1. 🌐 Go to Azure Portal:")
print("   https://portal.azure.com")

print("\n2. 🔍 Find or Create Azure Maps Account:")
print("   Option A: Search 'Azure Maps' in the search bar")
print("   Option B: Create new: 'Create a resource' → 'Azure Maps'")

print("\n3. 🔑 Get Subscription Key:")
print("   → Click on your Azure Maps account")
print("   → Go to 'Keys and Endpoint' (left sidebar)")
print("   → Copy 'Primary Key' or 'Secondary Key'")

print("\n4. 📝 Update your .env file:")
print("   AZURE_MAPS_SUBSCRIPTION_KEY=<your-new-key-here>")

print("\n5. 💰 Check Pricing Tier:")
print("   → Go to 'Pricing tier' in your Azure Maps account")
print("   → S0: Free tier (limited requests)")
print("   → S1: Pay-per-use (production)")

print("\n6. 🔒 Verify Permissions:")
print("   → Ensure your Azure subscription has Azure Maps enabled")
print("   → Check that the key has 'Reader' or 'Contributor' access")

print("\n7. 🧪 Test the new key:")
print("   → Update .env file with new key")
print("   → Run: python test_subscription_key.py")

print("\n💡 Common Issues:")
print("   • Old/expired subscription key")
print("   • Azure Maps service not enabled")
print("   • Incorrect pricing tier")
print("   • Network/firewall blocking requests")

print("\n📋 Your current .env file should have:")
print("   AZURE_MAPS_SUBSCRIPTION_KEY=<valid-key>")
print("   AZURE_MAPS_CLIENT_ID=<optional-for-managed-identity>")

print("\n🔗 Useful Links:")
print("   • Azure Maps Docs: https://docs.microsoft.com/en-us/azure/azure-maps/")
print("   • Pricing: https://azure.microsoft.com/en-us/pricing/details/azure-maps/")
print("   • REST API Docs: https://docs.microsoft.com/en-us/rest/api/maps/")
