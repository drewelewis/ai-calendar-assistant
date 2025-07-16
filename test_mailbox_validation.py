#!/usr/bin/env python3
"""
Test script to validate user mailboxes and troubleshoot Graph API calendar access issues.
This script helps identify why calendar access might be failing for specific users.
"""

import os
import asyncio
from dotenv import load_dotenv
from operations.graph_operations import GraphOperations

# Load environment variables
load_dotenv(override=True)

async def test_user_mailbox_validation():
    """Test mailbox validation for a specific user."""
    
    # Initialize Graph operations
    graph_ops = GraphOperations(
        user_response_fields=["id", "givenname", "surname", "displayname", "userprincipalname", "mail", "jobtitle", "department", "accountEnabled"],
        calendar_response_fields=["id", "subject", "start", "end", "location", "attendees"]
    )
    
    # Test user ID from your error log
    test_user_id = "07d4677a-e5dc-4f95-926e-4b953a37de78"
    
    print("🔍 Testing mailbox validation for problematic user...")
    print(f"   User ID: {test_user_id}")
    print("")
    
    # Step 1: Validate the user's mailbox
    print("1️⃣ Validating user mailbox...")
    validation_result = await graph_ops.validate_user_mailbox(test_user_id)
    
    print(f"   Valid: {validation_result['valid']}")
    print(f"   Message: {validation_result['message']}")
    
    if validation_result['user_info']:
        user = validation_result['user_info']
        print(f"   Display Name: {getattr(user, 'display_name', 'N/A')}")
        print(f"   Email: {getattr(user, 'mail', 'N/A')}")
        print(f"   UPN: {getattr(user, 'user_principal_name', 'N/A')}")
        print(f"   Account Enabled: {getattr(user, 'account_enabled', 'N/A')}")
    print("")
    
    # Step 2: Try to get basic user info
    print("2️⃣ Getting basic user information...")
    try:
        user = await graph_ops.get_user_by_user_id(test_user_id)
        if user:
            print(f"   ✅ User found: {getattr(user, 'display_name', 'N/A')}")
            print(f"   Email: {getattr(user, 'mail', 'N/A')}")
            print(f"   Job Title: {getattr(user, 'job_title', 'N/A')}")
            print(f"   Department: {getattr(user, 'department', 'N/A')}")
        else:
            print("   ❌ User not found")
    except Exception as e:
        print(f"   ❌ Error getting user: {e}")
    print("")
    
    # Step 3: Try calendar access (if validation passed)
    if validation_result['valid']:
        print("3️⃣ Attempting calendar access...")
        try:
            from datetime import datetime, timezone
            
            # Test with a specific date range
            start_date = datetime(2025, 7, 17, 0, 0, 0, tzinfo=timezone.utc)
            end_date = datetime(2025, 7, 17, 23, 59, 59, tzinfo=timezone.utc)
            
            events = await graph_ops.get_calendar_events_by_user_id(test_user_id, start_date, end_date)
            
            if events is not None:
                print(f"   ✅ Calendar access successful: {len(events)} events found")
                for i, event in enumerate(events[:3]):  # Show first 3 events
                    subject = getattr(event, 'subject', 'No subject')
                    print(f"      Event {i+1}: {subject}")
            else:
                print("   ❌ Calendar access failed (returned None)")
                
        except Exception as e:
            print(f"   ❌ Calendar access error: {e}")
    else:
        print("3️⃣ Skipping calendar access test (validation failed)")
    print("")
    
    # Step 4: Recommendations
    print("🎯 RECOMMENDATIONS:")
    if not validation_result['valid']:
        if "not found" in validation_result['message'].lower():
            print("   • Verify the user ID is correct")
            print("   • Check if the user exists in your Azure AD tenant")
        elif "mailbox" in validation_result['message'].lower():
            print("   • Contact your Exchange/Microsoft 365 administrator")
            print("   • Verify the user has an Exchange Online license")
            print("   • Check if the mailbox needs to be enabled for cloud access")
            print("   • For hybrid environments, ensure proper mailbox migration")
        elif "disabled" in validation_result['message'].lower():
            print("   • Re-enable the user account in Azure AD")
            print("   • Ensure the user has proper licenses assigned")
    else:
        print("   • Mailbox validation passed - calendar access should work")
        print("   • If still having issues, check application permissions")
        print("   • Ensure app has 'Calendars.Read' or 'Calendars.ReadWrite' permissions")

async def test_alternative_users():
    """Test with some alternative users to see if the issue is user-specific."""
    
    print("\n" + "="*60)
    print("🧪 TESTING ALTERNATIVE USERS")
    print("="*60)
    
    graph_ops = GraphOperations()
    
    # Try to find other users in the tenant
    print("1️⃣ Searching for other users in the tenant...")
    try:
        # Search for active users
        users = await graph_ops.search_users("accountEnabled eq true", max_results=5)
        
        if users:
            print(f"   Found {len(users)} active users")
            
            for i, user in enumerate(users[:3]):  # Test first 3 users
                user_id = getattr(user, 'id', None)
                display_name = getattr(user, 'display_name', 'Unknown')
                mail = getattr(user, 'mail', 'No email')
                
                print(f"\n2️⃣ Testing user {i+1}: {display_name}")
                print(f"   ID: {user_id}")
                print(f"   Email: {mail}")
                
                if user_id:
                    validation = await graph_ops.validate_user_mailbox(user_id)
                    print(f"   Mailbox Valid: {validation['valid']}")
                    if not validation['valid']:
                        print(f"   Issue: {validation['message']}")
        else:
            print("   No users found or access denied")
            
    except Exception as e:
        print(f"   Error searching users: {e}")

def main():
    """Main function to run the mailbox validation tests."""
    print("🔧 MAILBOX VALIDATION TEST TOOL")
    print("="*50)
    print("This tool helps diagnose Microsoft Graph calendar access issues.")
    print("")
    
    # Check environment variables
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
        return
    
    print("✅ Environment variables configured")
    print("")
    
    # Run the tests
    asyncio.run(test_user_mailbox_validation())
    asyncio.run(test_alternative_users())
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("="*60)
    print("1. Review the validation results above")
    print("2. If mailbox validation fails, contact your admin")
    print("3. If validation passes but calendar access fails, check app permissions")
    print("4. Consider using a different user ID for testing")
    print("5. Check Microsoft 365 admin center for user licensing and mailbox status")

if __name__ == "__main__":
    main()
