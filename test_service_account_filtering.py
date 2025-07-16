#!/usr/bin/env python3
"""
Test script to demonstrate mailbox filtering in Graph operations.
This script shows the difference between including and excluding users without active mailboxes.
"""

import os
import asyncio
from dotenv import load_dotenv
from operations.graph_operations import GraphOperations

# Load environment variables
load_dotenv(override=True)

async def test_mailbox_filtering():
    """Test mailbox filtering capabilities."""
    
    # Initialize Graph operations
    graph_ops = GraphOperations(
        user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "accountEnabled"],
        calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
    )
    
    print("🔍 TESTING MAILBOX FILTERING")
    print("="*60)
    
    # Test 1: Get all users WITHOUT filtering (includes users without mailboxes)
    print("\n1️⃣ Getting ALL users (including users without mailboxes)...")
    try:
        all_users_with_inactive = await graph_ops.get_all_users(max_results=50, exclude_inactive_mailboxes=False)
        print(f"   Found {len(all_users_with_inactive)} total users (including inactive mailboxes)")
        
        # Show some examples
        print("   Sample users (first 5):")
        for i, user in enumerate(all_users_with_inactive[:5]):
            display_name = getattr(user, 'display_name', 'N/A')
            upn = getattr(user, 'user_principal_name', 'N/A')
            mail = getattr(user, 'mail', 'No Email')
            account_enabled = getattr(user, 'account_enabled', 'N/A')
            print(f"      {i+1}. {display_name} ({upn}) - Email: {mail}, Enabled: {account_enabled}")
            
    except Exception as e:
        print(f"   Error: {e}")
        all_users_with_inactive = []
    
    # Test 2: Get all users WITH filtering (excludes users without mailboxes)
    print("\n2️⃣ Getting users with active mailboxes only...")
    try:
        users_with_mailboxes = await graph_ops.get_all_users(max_results=50, exclude_inactive_mailboxes=True)
        print(f"   Found {len(users_with_mailboxes)} users with active mailboxes")
        
        # Show some examples
        print("   Sample users with mailboxes (first 5):")
        for i, user in enumerate(users_with_mailboxes[:5]):
            display_name = getattr(user, 'display_name', 'N/A')
            upn = getattr(user, 'user_principal_name', 'N/A')
            mail = getattr(user, 'mail', 'No Email')
            account_enabled = getattr(user, 'account_enabled', 'N/A')
            print(f"      {i+1}. {display_name} ({upn}) - Email: {mail}, Enabled: {account_enabled}")
            
    except Exception as e:
        print(f"   Error: {e}")
        users_with_mailboxes = []
    
    # Test 3: Show the difference
    print("\n3️⃣ FILTERING RESULTS:")
    if all_users_with_inactive and users_with_mailboxes:
        inactive_mailboxes_filtered = len(all_users_with_inactive) - len(users_with_mailboxes)
        print(f"   📊 Total users: {len(all_users_with_inactive)}")
        print(f"   � Users with active mailboxes: {len(users_with_mailboxes)}")
        print(f"   ❌ Users without active mailboxes filtered out: {inactive_mailboxes_filtered}")
        
        if inactive_mailboxes_filtered > 0:
            print(f"   ✅ Successfully filtered out {inactive_mailboxes_filtered} users without active mailboxes!")
        else:
            print("   ℹ️ No users without active mailboxes found")
    
    # Test 4: Test search with two-stage filtering
    print("\n4️⃣ Testing search with two-stage mailbox filtering...")
    try:
        # Search for all enabled users
        search_with_inactive = await graph_ops.search_users("accountEnabled eq true", max_results=20, exclude_inactive_mailboxes=False)
        search_with_mailboxes = await graph_ops.search_users("accountEnabled eq true", max_results=20, exclude_inactive_mailboxes=True)
        
        print(f"   Search results (no mail filtering): {len(search_with_inactive)}")
        print(f"   Search results (with mail filtering): {len(search_with_mailboxes)}")
        
        if len(search_with_inactive) > len(search_with_mailboxes):
            filtered_count = len(search_with_inactive) - len(search_with_mailboxes)
            print(f"   🔧 Two-stage filtering removed {filtered_count} users without email addresses")
        
    except Exception as e:
        print(f"   Error in search test: {e}")

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "ENTRA_GRAPH_APPLICATION_TENANT_ID",
        "ENTRA_GRAPH_APPLICATION_CLIENT_ID", 
        "ENTRA_GRAPH_APPLICATION_CLIENT_SECRET"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\nPlease set these in your .env file before running the test.")
        return False
    
    return True

def main():
    """Main function to run the mailbox filtering tests."""
    print("🔧 MAILBOX FILTERING TEST")
    print("="*50)
    print("This tool demonstrates the ability to filter out users without active mailboxes.")
    print("")
    
    if not check_environment():
        return
    
    print("✅ Environment variables configured")
    print("")
    
    # Run the tests
    asyncio.run(test_mailbox_filtering())
    
    print("\n" + "="*60)
    print("🎯 SUMMARY:")
    print("="*60)
    print("✅ Mailbox filtering has been implemented!")
    print("")
    print("🔧 HOW IT WORKS:")
    print("• API-level filtering: Uses OData filters to get active users (accountEnabled eq true)")
    print("• Client-side filtering: Validates mailbox properties (account enabled + mail address)")
    print("• Graph API validation: Uses /mailboxSettings and /messages endpoints to verify mailbox")
    print("• RBAC compliant: Follows Microsoft's recommended approach for application permissions")
    print("• Error handling: Distinguishes between different mailbox error types")
    print("")
    print("🚀 USAGE:")
    print("• All user functions now have an 'exclude_inactive_mailboxes' parameter")
    print("• By default, users without mailboxes are excluded (exclude_inactive_mailboxes=True)")
    print("• Set exclude_inactive_mailboxes=False to include all users")
    print("")
    print("📝 WHAT'S FILTERED:")
    print("• Users with accountEnabled = false (API-level)")
    print("• Users without email addresses - mail = null (client-side)")
    print("• Focus on users with valid Exchange Online mailboxes")
    print("")
    print("🔍 VALIDATION METHOD:")
    print("• Uses Microsoft Graph /mailboxSettings endpoint (primary)")
    print("• Fallback to /messages endpoint if needed")
    print("• Detects ErrorMailboxNotEnabled and MailboxNotEnabledForRESTAPI")
    print("• Follows Microsoft's RBAC for Applications guidance")
    print("")
    print("⚠️  COMPATIBILITY NOTE:")
    print("• Uses two-stage filtering to avoid Graph API 'NotEqualsMatch' errors")
    print("• API filtering: accountEnabled eq true (supported)")
    print("• Client filtering: mailbox property validation (efficient)")

if __name__ == "__main__":
    main()
