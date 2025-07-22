#Requires -Modules Az.Accounts, Az.Resources

<#
.SYNOPSIS
    Remove administrative access for AI Calendar Assistant Azure resources
    
.DESCRIPTION
    This script removes administrative permissions from specified users across all Azure resources
    used by the AI Calendar Assistant solution.
    
.PARAMETER UserPrincipalName
    The User Principal Name (email) of the user to remove admin access from
    
.PARAMETER SubscriptionId
    The Azure subscription ID containing the resources (optional - will use current context if not provided)
    
.PARAMETER ResourceGroupName
    The resource group name containing the AI Calendar Assistant resources (optional - will search if not provided)
    
.PARAMETER WhatIf
    Show what actions would be performed without actually executing them
    
.EXAMPLE
    .\Remove-AdminAccess.ps1 -UserPrincipalName "john.doe@company.com"
    
.EXAMPLE
    .\Remove-AdminAccess.ps1 -UserPrincipalName "admin@company.com" -ResourceGroupName "ai-calendar-rg" -WhatIf
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$UserPrincipalName,
    
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $false)]
    [switch]$WhatIf
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Blue" = [ConsoleColor]::Blue
        "Cyan" = [ConsoleColor]::Cyan
        "Magenta" = [ConsoleColor]::Magenta
        "White" = [ConsoleColor]::White
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# Function to validate user exists in Azure AD
function Test-AzureADUser {
    param([string]$UserPrincipalName)
    
    try {
        $user = Get-AzADUser -UserPrincipalName $UserPrincipalName -ErrorAction Stop
        return $user
    }
    catch {
        Write-ColorOutput "❌ Error: User '$UserPrincipalName' not found in Azure AD" "Red"
        return $null
    }
}

# Main script execution
try {
    Write-ColorOutput "🗑️  AI Calendar Assistant - Remove Admin Access Script" "Cyan"
    Write-ColorOutput "=======================================================" "Cyan"
    
    # Check if user is logged in to Azure
    $context = Get-AzContext
    if (-not $context) {
        Write-ColorOutput "❌ Not logged in to Azure. Please run 'Connect-AzAccount' first." "Red"
        exit 1
    }
    
    # Set subscription context if provided
    if ($SubscriptionId) {
        try {
            Set-AzContext -SubscriptionId $SubscriptionId | Out-Null
            Write-ColorOutput "✅ Set subscription context to: $SubscriptionId" "Green"
        }
        catch {
            Write-ColorOutput "❌ Failed to set subscription context: $($_.Exception.Message)" "Red"
            exit 1
        }
    }
    
    $currentSub = (Get-AzContext).Subscription.Id
    Write-ColorOutput "📋 Using subscription: $currentSub" "Blue"
    Write-ColorOutput "👤 Removing admin access for: $UserPrincipalName" "Blue"
    
    # Validate user exists
    Write-ColorOutput "`n🔍 Validating user in Azure AD..." "Yellow"
    $targetUser = Test-AzureADUser -UserPrincipalName $UserPrincipalName
    if (-not $targetUser) {
        exit 1
    }
    Write-ColorOutput "✅ Found user: $($targetUser.DisplayName)" "Green"
    
    # Find resource group if not provided
    if (-not $ResourceGroupName) {
        Write-ColorOutput "`n🔍 Searching for AI Calendar Assistant resources..." "Yellow"
        
        # Look for resource groups with AI Calendar Assistant resources
        $candidateRGs = @()
        $allRGs = Get-AzResourceGroup
        
        foreach ($rg in $allRGs) {
            $resources = Get-AzResource -ResourceGroupName $rg.ResourceGroupName
            $hasCosmosDB = $resources | Where-Object { $_.ResourceType -eq "Microsoft.DocumentDB/databaseAccounts" -and $_.Name -like "*calendar*" }
            $hasContainerApp = $resources | Where-Object { $_.ResourceType -eq "Microsoft.App/containerApps" -and $_.Name -like "*wrapper*" }
            $hasOpenAI = $resources | Where-Object { $_.ResourceType -eq "Microsoft.CognitiveServices/accounts" -and $_.Kind -eq "OpenAI" }
            
            if ($hasCosmosDB -or $hasContainerApp -or $hasOpenAI) {
                $candidateRGs += $rg.ResourceGroupName
            }
        }
        
        if ($candidateRGs.Count -eq 0) {
            Write-ColorOutput "❌ Could not find AI Calendar Assistant resources. Please specify -ResourceGroupName parameter." "Red"
            exit 1
        }
        elseif ($candidateRGs.Count -eq 1) {
            $ResourceGroupName = $candidateRGs[0]
            Write-ColorOutput "✅ Found AI Calendar Assistant resources in: $ResourceGroupName" "Green"
        }
        else {
            Write-ColorOutput "❌ Found multiple resource groups with AI Calendar Assistant resources:" "Red"
            $candidateRGs | ForEach-Object { Write-ColorOutput "   - $_" "Yellow" }
            Write-ColorOutput "Please specify -ResourceGroupName parameter." "Red"
            exit 1
        }
    }
    
    # Get all role assignments for the user in the subscription
    Write-ColorOutput "`n🔍 Finding existing role assignments..." "Yellow"
    $allAssignments = Get-AzRoleAssignment -ObjectId $targetUser.Id | Where-Object { $_.Scope -like "*$currentSub*" }
    
    if ($allAssignments.Count -eq 0) {
        Write-ColorOutput "✅ No role assignments found for user in this subscription." "Green"
        exit 0
    }
    
    # Filter assignments related to our resource group and resources
    $relevantAssignments = $allAssignments | Where-Object { 
        $_.Scope -like "*$ResourceGroupName*" -or 
        $_.Scope -eq "/subscriptions/$currentSub/resourceGroups/$ResourceGroupName"
    }
    
    if ($relevantAssignments.Count -eq 0) {
        Write-ColorOutput "✅ No role assignments found for user in resource group '$ResourceGroupName'." "Green"
        exit 0
    }
    
    Write-ColorOutput "Found $($relevantAssignments.Count) role assignments to remove:" "Yellow"
    foreach ($assignment in $relevantAssignments) {
        $scopeParts = $assignment.Scope -split '/'
        $resourceName = if ($scopeParts.Count -gt 4) { $scopeParts[-1] } else { "Resource Group" }
        Write-ColorOutput "  • $($assignment.RoleDefinitionName) on $resourceName" "White"
    }
    
    # Confirm removal unless WhatIf
    if (-not $WhatIf) {
        Write-ColorOutput "`n⚠️  WARNING: This will remove ALL administrative access for user '$UserPrincipalName'" "Red"
        Write-ColorOutput "   from the AI Calendar Assistant resources." "Red"
        $confirmation = Read-Host "`nDo you want to continue? (yes/no)"
        
        if ($confirmation -ne "yes" -and $confirmation -ne "y") {
            Write-ColorOutput "❌ Operation cancelled by user." "Yellow"
            exit 0
        }
    }
    
    # Remove role assignments
    Write-ColorOutput "`n🗑️  Removing role assignments..." "Yellow"
    $successCount = 0
    $failureCount = 0
    
    foreach ($assignment in $relevantAssignments) {
        $scopeParts = $assignment.Scope -split '/'
        $resourceName = if ($scopeParts.Count -gt 4) { $scopeParts[-1] } else { "Resource Group '$ResourceGroupName'" }
        
        if ($WhatIf) {
            Write-ColorOutput "WHATIF: Would remove '$($assignment.RoleDefinitionName)' from $resourceName" "Cyan"
            $successCount++
        }
        else {
            try {
                Remove-AzRoleAssignment -ObjectId $assignment.ObjectId -RoleDefinitionName $assignment.RoleDefinitionName -Scope $assignment.Scope -ErrorAction Stop | Out-Null
                Write-ColorOutput "✅ Removed '$($assignment.RoleDefinitionName)' from $resourceName" "Green"
                $successCount++
            }
            catch {
                Write-ColorOutput "❌ Failed to remove '$($assignment.RoleDefinitionName)' from $resourceName : $($_.Exception.Message)" "Red"
                $failureCount++
            }
        }
    }
    
    # Summary
    Write-ColorOutput "`n" "White"
    Write-ColorOutput "📊 REMOVAL SUMMARY" "Cyan"
    Write-ColorOutput "==================" "Cyan"
    Write-ColorOutput "✅ Successfully removed: $successCount role assignments" "Green"
    if ($failureCount -gt 0) {
        Write-ColorOutput "❌ Failed to remove: $failureCount role assignments" "Red"
    }
    Write-ColorOutput "👤 User: $($targetUser.DisplayName) ($UserPrincipalName)" "Blue"
    Write-ColorOutput "📁 Resource Group: $ResourceGroupName" "Blue"
    
    if ($WhatIf) {
        Write-ColorOutput "`n💡 This was a simulation run. Use without -WhatIf to apply changes." "Yellow"
    } else {
        Write-ColorOutput "`n🎉 Admin access removal completed!" "Green"
        Write-ColorOutput "The user '$UserPrincipalName' no longer has administrative access to your AI Calendar Assistant." "Green"
    }
    
}
catch {
    Write-ColorOutput "❌ Script execution failed: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" "Red"
    exit 1
}
