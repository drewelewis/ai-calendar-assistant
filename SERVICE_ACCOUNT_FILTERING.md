# Service Account Filtering Guide

## Overview

The Microsoft Graph operations have been enhanced with comprehensive service account filtering to ensure that when you query for users, you get only regular human users and not system/service accounts that could clutter your results.

## What Are Service Accounts?

Service accounts are non-human accounts used by:
- Applications and services for authentication
- Automated processes and scheduled tasks
- System integrations and synchronization
- Backup and monitoring services
- Test and development environments

These accounts typically:
- Don't have personal names (given name/surname)
- Have technical or systematic naming patterns
- May be disabled or have different user types
- Don't have standard email addresses
- Are not meant for calendar scheduling or human interaction

## How the Filtering Works

### 1. API-Level Filtering (Server-Side)
The system applies OData filters directly to the Microsoft Graph API calls:

```odata
accountEnabled eq true and userType eq 'Member' and givenName ne null
```

This filters out:
- Disabled accounts
- Guest users (userType != 'Member')
- Accounts without given names

### 2. Client-Side Filtering (Application-Level)
Additional filtering happens in the application using the `_is_regular_user()` method:

**Checks for:**
- ✅ Must have both `givenName` and `surname`
- ✅ Must be `userType = 'Member'`
- ✅ Must be `accountEnabled = true`
- ❌ Rejects accounts with service naming patterns
- ❌ Rejects accounts with "service account" in display name

**Service Naming Patterns Detected:**
- UPN patterns: `service-`, `svc-`, `app-`, `system-`, `admin-`, `sync-`, `backup-`, `monitoring-`, `test-`, `automation-`, `robot-`, `bot-`, `scheduler-`
- Display name patterns: `service account`, `system account`, `admin account`, `sync account`, `backup account`, `test account`, `automation`, `scheduler`, `monitoring`

## Usage Examples

### 1. Get All Users (Default: Excludes Service Accounts)
```python
# Get regular users only (default behavior)
users = await graph_operations.get_all_users(max_results=100)

# Explicitly exclude service accounts
users = await graph_operations.get_all_users(max_results=100, exclude_service_accounts=True)

# Include service accounts if needed
all_users = await graph_operations.get_all_users(max_results=100, exclude_service_accounts=False)
```

### 2. Search Users (Default: Excludes Service Accounts)
```python
# Search for managers, excluding service accounts (default)
managers = await graph_operations.search_users("jobTitle eq 'Manager'", max_results=50)

# Search including service accounts if needed
all_managers = await graph_operations.search_users(
    "jobTitle eq 'Manager'", 
    max_results=50, 
    exclude_service_accounts=False
)
```

### 3. Get Users by Department (Default: Excludes Service Accounts)
```python
# Get IT department users, excluding service accounts (default)
it_users = await graph_operations.get_users_by_department("Information Technology", max_results=100)

# Include service accounts if needed for admin purposes
all_it_accounts = await graph_operations.get_users_by_department(
    "Information Technology", 
    max_results=100, 
    exclude_service_accounts=False
)
```

## Plugin Functions

All Graph plugin functions now support service account filtering:

### 1. user_search
```python
# Regular search (excludes service accounts by default)
users = await graph_plugin.user_search("department eq 'Engineering'")

# Include service accounts
users = await graph_plugin.user_search(
    "department eq 'Engineering'", 
    include_service_accounts=True
)
```

### 2. get_all_users
```python
# Get regular users (default)
users = await graph_plugin.get_all_users(max_results=100)

# Include service accounts
users = await graph_plugin.get_all_users(max_results=100, include_service_accounts=True)
```

### 3. get_users_by_department
```python
# Get department users (excludes service accounts by default)
users = await graph_plugin.get_users_by_department("Sales", max_results=50)

# Include service accounts
users = await graph_plugin.get_users_by_department(
    "Sales", 
    max_results=50, 
    include_service_accounts=True
)
```

## Benefits

### 1. Cleaner User Lists
- Calendar scheduling functions get only human users
- Meeting invitations won't include system accounts
- User searches return meaningful results

### 2. Better Performance
- Reduced data transfer by filtering out unwanted accounts
- Faster processing with smaller result sets
- More efficient API usage

### 3. Improved User Experience
- AI assistant provides more relevant user suggestions
- Reduced confusion from technical account names
- Focus on actual people for business operations

### 4. Flexible Control
- Default behavior excludes service accounts automatically
- Option to include service accounts when needed for admin tasks
- Maintains backward compatibility

## Testing

Run the service account filtering test to see the difference:

```bash
python test_service_account_filtering.py
```

This will show:
- Total users (including service accounts)
- Regular users (excluding service accounts)
- Number of service accounts filtered out
- Examples of both types

## Configuration

### Default Behavior
- **All user query functions default to excluding service accounts**
- This ensures calendar and meeting functions work with human users only
- No configuration changes needed for standard operation

### Including Service Accounts
When you need service accounts (for admin tasks, auditing, etc.):
- Set `exclude_service_accounts=False` in GraphOperations methods
- Set `include_service_accounts=True` in GraphPlugin methods

### Customizing Filtering
You can modify the `_is_regular_user()` method in `GraphOperations` to:
- Add new service account naming patterns
- Adjust filtering criteria
- Add organization-specific rules

## Example Output

```
📊 Filtered 47 raw users to 23 regular users (excluded service accounts)
```

This shows that 24 service accounts were automatically filtered out, leaving 23 regular users for your application to work with.

## AI Assistant Integration

The AI calendar assistant now:
- Automatically excludes service accounts from user searches
- Provides cleaner suggestions for meeting attendees
- Focuses on human users for scheduling operations
- Can include service accounts if specifically requested

This ensures a much better user experience when working with calendar and meeting scheduling functions.
