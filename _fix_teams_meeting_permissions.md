# Fix Teams Meeting Creation Permissions

## Error Diagnosis
The error "No application access policy found for this app" indicates missing application access policies for Teams meeting creation.

## Required Permissions
Your Azure AD app needs these permissions (with Admin Consent):

1. **OnlineMeetings.ReadWrite.All** (Application) ✅
2. **User.Read.All** (Application) ✅  
3. **Calendars.ReadWrite** (Application) ✅

**✅ YOUR PERMISSIONS ARE CORRECT!** The issue is the missing Teams Application Access Policy.

## PowerShell Commands to Fix

### 1. Install Required Module
```powershell
Install-Module -Name MicrosoftTeams -Force
```

### 2. Connect to Teams
```powershell
Connect-MicrosoftTeams
```

### 3. Create Application Access Policy
```powershell
# Your actual Azure AD Application ID from .env file
$AppId = yourapp id

# Create the policy (allows the app to create meetings for all users)
New-CsApplicationAccessPolicy -Identity "TeamsGraphAppPolicy" -AppIds $AppId -Description "Policy to allow Graph app to create Teams meetings"
```

### 4. Apply Policy Globally (Option 1 - All Users)
```powershell
Grant-CsApplicationAccessPolicy -PolicyName "TeamsGraphAppPolicy" -Global
```

### 4. Apply Policy to Specific Users (Option 2 - Specific Users)
```powershell
# Replace with actual user UPNs who need Teams meeting creation
Grant-CsApplicationAccessPolicy -PolicyName "TeamsGraphAppPolicy" -Identity "user@yourdomain.com"
Grant-CsApplicationAccessPolicy -PolicyName "TeamsGraphAppPolicy" -Identity "another.user@yourdomain.com"
```

### 5. Verify Policy
```powershell
Get-CsApplicationAccessPolicy -Identity "TeamsGraphAppPolicy"
```

## Alternative: Azure CLI Commands

### 1. Login to Azure
```bash
az login
```

### 2. Set Your Subscription
```bash
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### 3. Check App Permissions
```bash
az ad app permission list --id YOUR_APP_ID
```

## Environment Variables to Check
Make sure these are set correctly:
- `ENTRA_GRAPH_APPLICATION_TENANT_ID`
- `ENTRA_GRAPH_APPLICATION_CLIENT_ID`
- `ENTRA_GRAPH_APPLICATION_CLIENT_SECRET`

## Test After Fixing
1. Wait 5-10 minutes for policy propagation
2. Run your Teams meeting creation test
3. Check for successful meeting creation

## Troubleshooting
- **Still getting 403?** Wait longer for policy propagation (up to 30 minutes)
- **Permission denied in PowerShell?** Make sure you're a Teams admin
- **App not found?** Verify your App ID is correct
- **Policy not working?** Try applying to specific users first, then global

## Security Note
The global policy allows your app to create meetings for ALL users in your tenant. For production, consider applying only to specific users or groups who need this functionality.
