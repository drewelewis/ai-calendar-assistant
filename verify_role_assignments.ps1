# Azure Role Assignment Verification (PowerShell)
# This script checks role assignments for your managed identity

$identityId = "5238e629-da2f-4bb0-aea5-14d45526c864"

Write-Host "🔍 Azure Role Assignment Verification" -ForegroundColor Cyan
Write-Host "=" * 50
Write-Host "Managed Identity: $identityId" -ForegroundColor Yellow
Write-Host ""

# Check if Azure CLI is available
try {
    $azVersion = az --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI not found"
    }
    Write-Host "✅ Azure CLI is available" -ForegroundColor Green
}
catch {
    Write-Host "❌ Azure CLI not available" -ForegroundColor Red
    Write-Host "💡 Install Azure CLI or use Azure Cloud Shell" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
try {
    $account = az account show 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) {
        throw "Not logged in"
    }
    Write-Host "✅ Logged into Azure CLI" -ForegroundColor Green
    Write-Host "   Subscription: $($account.name)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Not logged into Azure CLI" -ForegroundColor Red
    Write-Host "💡 Run 'az login' first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Get role assignments
Write-Host "📋 Checking Role Assignments..." -ForegroundColor Cyan
try {
    $assignments = az role assignment list --assignee $identityId | ConvertFrom-Json
    
    if ($assignments.Count -eq 0) {
        Write-Host "❌ NO ROLE ASSIGNMENTS FOUND!" -ForegroundColor Red
        Write-Host "💡 This is the problem - your managed identity has no roles." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🔧 TO FIX:" -ForegroundColor Green
        Write-Host "1. Go to Azure Portal → Azure Maps → Access Control (IAM)"
        Write-Host "2. Add role assignment: 'Azure Maps Data Reader'"
        Write-Host "3. Assign to your Container App's managed identity"
        exit 1
    }
    
    Write-Host "Found $($assignments.Count) role assignment(s):" -ForegroundColor Green
    Write-Host ""
    
    $mapsReaderFound = $false
    for ($i = 0; $i -lt $assignments.Count; $i++) {
        $assignment = $assignments[$i]
        $roleNumber = $i + 1
        
        Write-Host "Assignment $roleNumber:" -ForegroundColor White
        Write-Host "   • Role: $($assignment.roleDefinitionName)" -ForegroundColor Gray
        Write-Host "   • Scope: $($assignment.scope)" -ForegroundColor Gray
        Write-Host "   • Type: $($assignment.principalType)" -ForegroundColor Gray
        
        if ($assignment.roleDefinitionName -like "*Azure Maps Data Reader*") {
            $mapsReaderFound = $true
            Write-Host "   ✅ Found Azure Maps Data Reader role!" -ForegroundColor Green
            
            if ($assignment.scope -like "*/providers/Microsoft.Maps/accounts/*") {
                Write-Host "   ✅ Scope is at Azure Maps account level" -ForegroundColor Green
                Write-Host "   ✅ This should work - role assignment looks correct" -ForegroundColor Green
            }
            elseif ($assignment.scope -like "*/resourceGroups/*" -and $assignment.scope -notlike "*/providers/Microsoft.Maps/accounts/*") {
                Write-Host "   ⚠️  Scope is at Resource Group level" -ForegroundColor Yellow
                Write-Host "   💡 This might work, but Azure Maps account level is preferred" -ForegroundColor Yellow
            }
            elseif ($assignment.scope -like "/subscriptions/*" -and $assignment.scope -notlike "*/resourceGroups/*") {
                Write-Host "   ⚠️  Scope is at Subscription level" -ForegroundColor Yellow
                Write-Host "   💡 This should work but is overly broad" -ForegroundColor Yellow
            }
            else {
                Write-Host "   ❌ Scope is unclear or incorrect" -ForegroundColor Red
            }
        }
        else {
            Write-Host "   ⚠️  Not an Azure Maps role" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    if (-not $mapsReaderFound) {
        Write-Host "❌ NO AZURE MAPS DATA READER ROLE FOUND!" -ForegroundColor Red
        Write-Host "💡 This is the problem!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🔧 TO FIX:" -ForegroundColor Green
        Write-Host "1. Go to Azure Portal → Azure Maps → Access Control (IAM)"
        Write-Host "2. Add role assignment: 'Azure Maps Data Reader'"
        Write-Host "3. Assign to your Container App's managed identity"
        exit 1
    }
}
catch {
    Write-Host "❌ Failed to get role assignments: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# List Azure Maps accounts
Write-Host "🗺️ Available Azure Maps Accounts" -ForegroundColor Cyan
Write-Host "=" * 40
try {
    $mapsAccounts = az maps account list | ConvertFrom-Json
    
    if ($mapsAccounts.Count -eq 0) {
        Write-Host "❌ No Azure Maps accounts found" -ForegroundColor Red
        exit 1
    }
    
    for ($i = 0; $i -lt $mapsAccounts.Count; $i++) {
        $account = $mapsAccounts[$i]
        $accountNumber = $i + 1
        
        Write-Host "Account $accountNumber:" -ForegroundColor White
        Write-Host "   • Name: $($account.name)" -ForegroundColor Gray
        Write-Host "   • Resource Group: $($account.resourceGroup)" -ForegroundColor Gray
        Write-Host "   • Location: $($account.location)" -ForegroundColor Gray
        Write-Host "   • Full ID: $($account.id)" -ForegroundColor Gray
        Write-Host ""
        
        # Check role assignments for this specific account
        Write-Host "   🔍 Checking role assignments for this account..." -ForegroundColor Cyan
        try {
            $scopeAssignments = az role assignment list --assignee $identityId --scope $account.id | ConvertFrom-Json
            
            if ($scopeAssignments.Count -gt 0) {
                Write-Host "   ✅ Found $($scopeAssignments.Count) role assignment(s) for this account" -ForegroundColor Green
                foreach ($scopeAssignment in $scopeAssignments) {
                    Write-Host "      - $($scopeAssignment.roleDefinitionName)" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "   ❌ No role assignments found for this specific account" -ForegroundColor Red
                Write-Host "   💡 Try assigning 'Azure Maps Data Reader' to this account specifically" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "   ⚠️  Could not check role assignments for this account" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}
catch {
    Write-Host "❌ Failed to list Azure Maps accounts: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "📊 SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 20
if ($mapsReaderFound) {
    Write-Host "✅ Azure Maps Data Reader role is assigned" -ForegroundColor Green
    Write-Host "🤔 If you're still getting 401 errors:" -ForegroundColor Yellow
    Write-Host "   • Wait 15 minutes for propagation"
    Write-Host "   • Restart your Container App"
    Write-Host "   • Verify you're using the correct Azure Maps account"
    Write-Host "   • Check Azure Maps account is in the same region"
}
else {
    Write-Host "❌ Missing or incorrect role assignment" -ForegroundColor Red
    Write-Host "💡 Follow the fix instructions above" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
