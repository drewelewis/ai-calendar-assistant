#!/usr/bin/env python3
"""
Test script to verify the updated environment-aware authentication.
Tests both Azure Identity and key-based authentication based on environment.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test the new authentication logic
from identity.azure_credentials import AzureCredentials
from storage.cosmosdb_chat_history_manager import CosmosDBChatHistoryManager

def test_authentication():
    """Test the new environment-aware authentication"""
    print("🧪 Testing Environment-Aware Authentication")
    print("=" * 50)
    
    current_env = os.getenv("ENVIRONMENT", "production")
    print(f"Current ENVIRONMENT setting: {current_env}")
    print()
    
    # Test 1: Azure credential retrieval
    try:
        print("1️⃣ Testing Azure credential retrieval...")
        credential = AzureCredentials.get_credential()
        print("✅ Azure Identity authentication successful!")
        azure_auth_success = True
    except Exception as e:
        print(f"❌ Azure Identity authentication failed: {e}")
        azure_auth_success = False
    
    print()
    
    # Test 2: Cosmos DB connection with environment awareness
    try:
        print("2️⃣ Testing Cosmos DB connection...")
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        cosmos_database = os.getenv("COSMOS_DATABASE", "CalendarAssistant")
        cosmos_container = os.getenv("COSMOS_CONTAINER", "ChatHistory")
        
        if not cosmos_endpoint:
            print("❌ COSMOS_ENDPOINT not set in environment")
            return False
        
        print(f"   Endpoint: {cosmos_endpoint}")
        print(f"   Environment: {current_env}")
        print(f"   Key-based fallback allowed: {'Yes' if current_env.lower() in ['development', 'local', 'dev'] else 'No (Production)'}")
        
        manager = CosmosDBChatHistoryManager(cosmos_endpoint, cosmos_database, cosmos_container)
        print("✅ Cosmos DB connection successful!")
        cosmos_auth_success = True
    except Exception as e:
        print(f"❌ Cosmos DB connection failed: {e}")
        cosmos_auth_success = False
    
    return azure_auth_success or cosmos_auth_success

def test_environment_scenarios():
    """Test different environment scenarios"""
    print("\n🔄 Testing Different Environment Scenarios")
    print("=" * 50)
    
    original_env = os.getenv("ENVIRONMENT")
    
    # Test development environment
    print("\n🔧 Testing Development Environment:")
    os.environ["ENVIRONMENT"] = "development"
    test_authentication()
    
    # Test production environment
    print("\n🚀 Testing Production Environment:")
    os.environ["ENVIRONMENT"] = "production"
    test_authentication()
    
    # Restore original environment
    if original_env:
        os.environ["ENVIRONMENT"] = original_env
    else:
        os.environ.pop("ENVIRONMENT", None)

if __name__ == "__main__":
    success = test_authentication()
    
    # Run environment scenario tests
    test_environment_scenarios()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 Authentication logic is working!")
        print()
        print("✅ Key findings:")
        print(f"   • Environment: {os.getenv('ENVIRONMENT', 'production')}")
        print(f"   • Key fallback: {'Enabled' if os.getenv('ENVIRONMENT', 'production').lower() in ['development', 'local', 'dev'] else 'DISABLED (Production)'}")
        print()
        print("📋 Next steps:")
        print("1. Deploy updated code to Container App")
        print("2. Verify Container App has ENVIRONMENT=production")
        print("3. Ensure Container App does NOT have COSMOS_KEY")
        print("4. Test the application with managed identity only")
    else:
        print("❌ Authentication test failed.")
        print()
        print("🔍 Troubleshooting:")
        current_env = os.getenv("ENVIRONMENT", "production").lower()
        if current_env in ["development", "local", "dev"]:
            print("   • For development: Ensure you're logged in with 'az login'")
            print("   • Or set COSMOS_KEY in your .env file for key-based fallback")
        else:
            print("   • For production: Managed Identity must be properly configured")
            print("   • Key-based authentication is disabled in production for security")
