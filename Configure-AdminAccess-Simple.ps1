# AI Calendar Assistant - Admin Access Configuration Script (Simplified)
# This version installs required modules as needed instead of requiring them upfront

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

# Function to install required modules
function Install-RequiredModules {
    $requiredModules = @(
        "Az.Accounts",
        "Az.Resources", 
        "Az.Profile"
    )
    
    Write-ColorOutput "🔧 Checking and installing required Azure PowerShell modules..." "Yellow"
    
    foreach ($module in $requiredModules) {
        if (!(Get-Module -ListAvailable -Name $module)) {
            Write-ColorOutput "Installing module: $module" "Blue"
            try {
                Install-Module -Name $module -Force -AllowClobber -Scope CurrentUser -ErrorAction Stop
                Write-ColorOutput "✅ Successfully installed $module" "Green"
            }
            catch {
                Write-ColorOutput "❌ Failed to install $module`: $($_.Exception.Message)" "Red"
                return $false
            }
        } else {
            Write-ColorOutput "✅ Module $module is already installed" "Green"
        }
    }
    return $true
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
        Write-ColorOutput "   Please verify the email address is correct and the user exists in your tenant" "Yellow"
        return $null
    }
}

# Function to assign role with error handling
function Set-ResourceRole {
    param(
        [string]$Scope,
        [string]$RoleDefinitionName,
        [string]$ObjectId,
        [string]$ResourceName,
        [string]$ResourceType
    )
    
    if ($WhatIf) {
        Write-ColorOutput "WHATIF: Would assign '$RoleDefinitionName' role to user on $ResourceType '$ResourceName'" "Cyan"
        return $true
    }
    
    try {
        $existingAssignment = Get-AzRoleAssignment -Scope $Scope -RoleDefinitionName $RoleDefinitionName -ObjectId $ObjectId -ErrorAction SilentlyContinue
        
        if ($existingAssignment) {
            Write-ColorOutput "✅ Role '$RoleDefinitionName' already assigned on $ResourceType '$ResourceName'" "Yellow"
            return $true
        }
        
        New-AzRoleAssignment -Scope $Scope -RoleDefinitionName $RoleDefinitionName -ObjectId $ObjectId -ErrorAction Stop | Out-Null
        Write-ColorOutput "✅ Successfully assigned '$RoleDefinitionName' role on $ResourceType '$ResourceName'" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "❌ Failed to assign '$RoleDefinitionName' role on $ResourceType '$ResourceName': $($_.Exception.Message)" "Red"
        return $false
    }
}

# Main script execution
try {
    Write-ColorOutput "🚀 AI Calendar Assistant - Admin Access Configuration Script" "Cyan"
    Write-ColorOutput "============================================================" "Cyan"
    
    # Install required modules
    if (!(Install-RequiredModules)) {
        Write-ColorOutput "❌ Failed to install required modules. Exiting." "Red"
        exit 1
    }
    
    # Import required modules
    Import-Module Az.Accounts -Force
    Import-Module Az.Resources -Force
    
    # Check if user is logged in to Azure
    $context = Get-AzContext
    if (-not $context) {
        Write-ColorOutput "❌ Not logged in to Azure. Attempting to login..." "Yellow"
        try {
            Connect-AzAccount
            $context = Get-AzContext
            if (-not $context) {
                Write-ColorOutput "❌ Failed to login to Azure. Please run 'Connect-AzAccount' manually." "Red"
                exit 1
            }
        }
        catch {
            Write-ColorOutput "❌ Failed to login to Azure: $($_.Exception.Message)" "Red"
            exit 1
        }
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
    Write-ColorOutput "👤 Configuring admin access for: $UserPrincipalName" "Blue"
    
    # Validate user exists
    Write-ColorOutput "`n🔍 Validating user in Azure AD..." "Yellow"
    $targetUser = Test-AzureADUser -UserPrincipalName $UserPrincipalName
    if (-not $targetUser) {
        exit 1
    }
    Write-ColorOutput "✅ Found user: $($targetUser.DisplayName)" "Green"
    
    # Use provided resource group
    if (-not $ResourceGroupName) {
        $ResourceGroupName = "devops-ai-rg"  # Default from your .env file
        Write-ColorOutput "📁 Using default resource group: $ResourceGroupName" "Blue"
    }
    
    # Get all resources in the resource group
    Write-ColorOutput "`n📋 Discovering resources in '$ResourceGroupName'..." "Yellow"
    $resources = Get-AzResource -ResourceGroupName $ResourceGroupName -ErrorAction SilentlyContinue
    
    if (-not $resources -or $resources.Count -eq 0) {
        Write-ColorOutput "❌ No resources found in resource group '$ResourceGroupName'" "Red"
        Write-ColorOutput "Please verify the resource group name is correct." "Yellow"
        exit 1
    }
    
    Write-ColorOutput "✅ Found $($resources.Count) resources to configure" "Green"
    
    # Role assignment tracking
    $successCount = 0
    $failureCount = 0
    
    Write-ColorOutput "`n🔧 Configuring administrative access..." "Yellow"
    Write-ColorOutput "==========================================" "Yellow"
    
    # 1. Resource Group level permissions
    Write-ColorOutput "`n📁 Resource Group: $ResourceGroupName" "Magenta"
    $rgScope = "/subscriptions/$currentSub/resourceGroups/$ResourceGroupName"
    
    # Contributor role for general management
    if (Set-ResourceRole -Scope $rgScope -RoleDefinitionName "Contributor" -ObjectId $targetUser.Id -ResourceName $ResourceGroupName -ResourceType "Resource Group") {
        $successCount++
    } else {
        $failureCount++
    }
    
    # 2. Process each resource individually for specific permissions
    foreach ($resource in $resources) {
        $resourceScope = $resource.ResourceId
        Write-ColorOutput "`n🔧 $($resource.ResourceType): $($resource.Name)" "Magenta"
        
        # Assign Contributor role to all resources (simplified approach)
        if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType $resource.ResourceType) {
            $successCount++
        } else {
            $failureCount++
        }
        
        # Add specific roles for key resource types
        switch ($resource.ResourceType) {
            "Microsoft.DocumentDB/databaseAccounts" {
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "DocumentDB Account Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Cosmos DB") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
            
            "Microsoft.CognitiveServices/accounts" {
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Cognitive Services User" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Azure OpenAI") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
            
            "Microsoft.Insights/components" {
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Monitoring Reader" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Application Insights") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
        }
    }
    
    # Summary
    Write-ColorOutput "`n" "White"
    Write-ColorOutput "📊 CONFIGURATION SUMMARY" "Cyan"
    Write-ColorOutput "=========================" "Cyan"
    Write-ColorOutput "✅ Successful role assignments: $successCount" "Green"
    if ($failureCount -gt 0) {
        Write-ColorOutput "❌ Failed role assignments: $failureCount" "Red"
    }
    Write-ColorOutput "👤 User configured: $($targetUser.DisplayName) ($UserPrincipalName)" "Blue"
    Write-ColorOutput "📁 Resource Group: $ResourceGroupName" "Blue"
    Write-ColorOutput "🔧 Resources configured: $($resources.Count)" "Blue"
    
    if ($WhatIf) {
        Write-ColorOutput "`n💡 This was a simulation run. Use without -WhatIf to apply changes." "Yellow"
    } else {
        Write-ColorOutput "`n🎉 Admin access configuration completed!" "Green"
        Write-ColorOutput "The user '$UserPrincipalName' now has administrative access to your AI Calendar Assistant." "Green"
    }
    
    # Additional guidance
    Write-ColorOutput "`n📚 ADMIN USER GUIDANCE" "Cyan"
    Write-ColorOutput "=======================" "Cyan"
    Write-ColorOutput "The configured admin user can now:" "White"
    Write-ColorOutput "• Monitor application health and performance" "White"
    Write-ColorOutput "• View and analyze logs in Application Insights" "White"
    Write-ColorOutput "• Manage container app scaling and configuration" "White"
    Write-ColorOutput "• Access Cosmos DB data and manage collections" "White"
    Write-ColorOutput "• Configure Azure OpenAI deployments and settings" "White"
    Write-ColorOutput "• Manage Redis cache configuration" "White"
    Write-ColorOutput "• Update bot service settings and channels" "White"
    Write-ColorOutput "• Access Azure Maps configuration" "White"
    Write-ColorOutput "`nNext steps for the admin user:" "Yellow"
    Write-ColorOutput "1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" "White"
    Write-ColorOutput "2. Install Azure PowerShell: Install-Module -Name Az" "White"
    Write-ColorOutput "3. Login: Connect-AzAccount" "White"
    Write-ColorOutput "4. Access Azure Portal: https://portal.azure.com" "White"
    
}
catch {
    Write-ColorOutput "❌ Script execution failed: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" "Red"
    exit 1
}
