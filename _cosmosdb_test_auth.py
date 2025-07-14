#!/usr/bin/env python3
"""
Test script to verify CosmosDB authentication setup.
Run this script to check if your Azure authentication is working correctly.
"""

import os
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential, EnvironmentCredential, ManagedIdentityCredential
from azure.core.exceptions import ClientAuthenticationError
from dotenv import load_dotenv

def test_azure_credential():
    """Test Azure credential authentication"""
    print("Testing Azure authentication methods...")
    
    credentials_to_test = [
        ("Environment Credential", EnvironmentCredential()),
        ("Managed Identity Credential", ManagedIdentityCredential()),
        ("Default Azure Credential", DefaultAzureCredential())
    ]
    
    working_credential = None
    
    for name, credential in credentials_to_test:
        try:
            print(f"  Trying {name}...")
            token = credential.get_token("https://cosmos.azure.com/.default")
            if token:
                print(f"  ✓ {name} authentication successful!")
                working_credential = credential
                break
        except Exception as e:
            print(f"  ✗ {name} failed: {e}")
    
    return working_credential

def test_cosmos_connection():
    """Test CosmosDB connection with Azure Identity"""
    load_dotenv()
    
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    if not cosmos_endpoint:
        print("Error: COSMOS_ENDPOINT environment variable not set")
        return False
    
    print(f"\nTesting connection to CosmosDB: {cosmos_endpoint}")
    
    # Test authentication
    credential = test_azure_credential()
    if not credential:
        print("Error: No working Azure credential found")
        return False
    
    # Test CosmosDB connection
    try:
        client = CosmosClient(cosmos_endpoint, credential=credential)
        
        # Try to list databases (this will fail if permissions are insufficient)
        databases = list(client.list_databases())
        print(f"✓ Successfully connected to CosmosDB!")
        print(f"  Found {len(databases)} databases")
        
        return True
        
    except ClientAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure you're logged in: az login")
        print("2. Check RBAC permissions on CosmosDB account")
        print("3. Verify local authorization is disabled on CosmosDB")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("CosmosDB Azure Authentication Test")
    print("=" * 40)
    
    success = test_cosmos_connection()
    
    if success:
        print("\n🎉 Authentication setup is working correctly!")
    else:
        print("\n❌ Authentication setup needs attention. See _cosmosdb_auth_setup.md for help.")
