# Microsoft Graph Calendar Access Issue - Troubleshooting Guide

## Problem Summary
You're encountering a `MailboxNotEnabledForRESTAPI` error when trying to access calendar events for user ID `07d4677a-e5dc-4f95-926e-4b953a37de78`. This error indicates that the user's mailbox is not available for Graph API access.

## Root Cause
The error message "The mailbox is either inactive, soft-deleted, or is hosted on-premise" means:

1. **Inactive Mailbox**: User doesn't have an active Exchange Online mailbox
2. **Soft-deleted**: Mailbox was recently deleted but still in recovery period
3. **On-premise**: User's mailbox is hosted on on-premise Exchange server
4. **No License**: User lacks proper Microsoft 365/Exchange Online licensing

## Implemented Solutions

### 1. Enhanced Error Handling
- Added detailed error diagnosis in `graph_operations.py`
- Provides specific guidance for different error types
- Includes actionable troubleshooting steps

### 2. Mailbox Validation Function
- New `validate_user_mailbox()` method to check mailbox status before calendar access
- Validates user existence, mail property, and account status
- Returns detailed validation results with diagnostic information

### 3. New Plugin Function
- Added `validate_user_mailbox` function to `GraphPlugin`
- Allows AI agent to proactively check mailbox status
- Provides user-friendly error messages

### 4. Improved Error Context
- Enhanced `get_calendar_events` function with better error handling
- Returns meaningful error information instead of generic failures
- Includes troubleshooting tips in error messages

### 5. Test Tool
- Created `test_mailbox_validation.py` script for troubleshooting
- Tests specific user IDs and provides diagnostic information
- Helps identify root cause of mailbox issues

## How to Use the Improvements

### 1. Run the Test Tool
```cmd
python test_mailbox_validation.py
```
This will test the problematic user ID and provide detailed diagnostics.

### 2. Use Mailbox Validation in Your Code
```python
# Before accessing calendar, validate the mailbox
validation = await graph_operations.validate_user_mailbox(user_id)
if not validation['valid']:
    print(f"Cannot access calendar: {validation['message']}")
    return None
```

### 3. AI Agent Improvements
The AI agent now has:
- Better error handling instructions in prompts
- Access to mailbox validation function
- Improved error communication to users

## Administrative Solutions

### For IT Administrators:
1. **Check User Licensing**:
   - Ensure user has Exchange Online license
   - Verify Microsoft 365 subscription includes calendar access

2. **Mailbox Status**:
   - Check Microsoft 365 admin center for mailbox status
   - Verify mailbox is not soft-deleted or disabled

3. **Hybrid Environments**:
   - For on-premise Exchange, ensure proper hybrid configuration
   - Consider migrating mailbox to Exchange Online

4. **User Account**:
   - Verify user account is active and enabled
   - Check that user has completed initial setup

### For Developers:
1. **Application Permissions**:
   - Ensure app has `Calendars.Read` or `Calendars.ReadWrite` permissions
   - Verify admin consent has been granted for application permissions

2. **Alternative Approaches**:
   - Use different user IDs for testing
   - Implement graceful fallbacks when calendar access fails
   - Cache successful user validations to avoid repeated checks

## Quick Fixes to Try

1. **Test with Different Users**:
   ```bash
   # Run the test tool to find users with working mailboxes
   python test_mailbox_validation.py
   ```

2. **Check User in Admin Center**:
   - Go to Microsoft 365 admin center
   - Search for the user ID
   - Verify Exchange license and mailbox status

3. **Use Working User ID**:
   - Find a user with active mailbox
   - Update your test cases to use validated user IDs

4. **Enable Diagnostic Logging**:
   - The improved error handling now provides detailed diagnostic information
   - Check console output for specific guidance

## Prevention

1. **Always Validate First**:
   - Use `validate_user_mailbox()` before calendar operations
   - Handle validation failures gracefully

2. **Implement Retry Logic**:
   - For transient errors, implement exponential backoff
   - Cache validation results to reduce API calls

3. **User-Friendly Messaging**:
   - Provide clear explanations when calendar access fails
   - Suggest alternative actions or contact information

## Code Examples

### Validating Before Calendar Access:
```python
async def safe_get_calendar_events(user_id, start_date, end_date):
    # First validate the mailbox
    validation = await graph_operations.validate_user_mailbox(user_id)
    
    if not validation['valid']:
        return {
            'success': False,
            'error': validation['message'],
            'events': []
        }
    
    # Proceed with calendar access
    try:
        events = await graph_operations.get_calendar_events_by_user_id(
            user_id, start_date, end_date
        )
        return {
            'success': True,
            'events': events or [],
            'user_info': validation['user_info']
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Calendar access failed: {e}",
            'events': []
        }
```

### AI Agent Error Handling:
The AI agent now automatically:
- Validates mailboxes before calendar operations
- Provides clear error explanations to users
- Suggests alternative actions when calendar access fails

## Next Steps

1. Run the test tool to diagnose the specific issue
2. Check with your Microsoft 365 administrator about user licensing
3. Consider using alternative user IDs for testing
4. Monitor error patterns to identify systemic issues
5. Implement the validation functions in your production workflow

The enhanced error handling should now provide much better diagnostics and user experience when mailbox issues occur.
