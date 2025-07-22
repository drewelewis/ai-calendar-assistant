#Requires -Modules Az.Accounts, Az.Resources, Az.ContainerInstance, Az.CosmosDB, Az.OperationalInsights, Az.CognitiveServices, Az.Maps, Az.BotService, Az.WebSites

<#
.SYNOPSIS
    Configure administrative access for AI Calendar Assistant Azure resources
    
.DESCRIPTION
    This script grants administrative permissions to specified users across all Azure resources
    used by the AI Calendar Assistant solution, enabling them to manage the system when you're away.
    
.PARAMETER UserPrincipalName
    The User Principal Name (email) of the user to grant admin access to
    
.PARAMETER SubscriptionId
    The Azure subscription ID containing the resources (optional - will use current context if not provided)
    
.PARAMETER ResourceGroupName
    The resource group name containing the AI Calendar Assistant resources (optional - will search if not provided)
    
.PARAMETER WhatIf
    Show what actions would be performed without actually executing them
    
.EXAMPLE
    .\Configure-AdminAccess.ps1 -UserPrincipalName "john.doe@company.com"
    
.EXAMPLE
    .\Configure-AdminAccess.ps1 -UserPrincipalName "admin@company.com" -ResourceGroupName "ai-calendar-rg" -WhatIf
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
    Write-ColorOutput "👤 Configuring admin access for: $UserPrincipalName" "Blue"
    
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
    
    # Get all resources in the resource group
    Write-ColorOutput "`n📋 Discovering resources in '$ResourceGroupName'..." "Yellow"
    $resources = Get-AzResource -ResourceGroupName $ResourceGroupName
    
    if ($resources.Count -eq 0) {
        Write-ColorOutput "❌ No resources found in resource group '$ResourceGroupName'" "Red"
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
        
        switch ($resource.ResourceType) {
            "Microsoft.DocumentDB/databaseAccounts" {
                # Cosmos DB specific roles
                $roles = @("DocumentDB Account Contributor", "Cosmos DB Account Reader Role")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Cosmos DB") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.App/containerApps" {
                # Container Apps specific roles
                $roles = @("ContainerApp Reader", "Contributor")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Container App") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.App/managedEnvironments" {
                # Container App Environment
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Container App Environment") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
            
            "Microsoft.CognitiveServices/accounts" {
                # Azure OpenAI specific roles
                $roles = @("Cognitive Services OpenAI Contributor", "Cognitive Services User")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Azure OpenAI") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.Cache/Redis" {
                # Redis Cache
                $roles = @("Redis Cache Contributor", "Contributor")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Redis Cache") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.Insights/components" {
                # Application Insights
                $roles = @("Application Insights Component Contributor", "Monitoring Reader")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Application Insights") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.OperationalInsights/workspaces" {
                # Log Analytics
                $roles = @("Log Analytics Contributor", "Log Analytics Reader")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Log Analytics") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.Maps/accounts" {
                # Azure Maps
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Azure Maps") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
            
            "Microsoft.BotService/botServices" {
                # Azure Bot Service
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Bot Service") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
            
            "Microsoft.Web/sites" {
                # App Service
                $roles = @("Website Contributor", "Web Plan Contributor")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "App Service") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            "Microsoft.Web/serverfarms" {
                # App Service Plan
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Web Plan Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "App Service Plan") {
                    $successCount++
                } else {
                    $failureCount++
                }
            }
            
            "Microsoft.ManagedIdentity/userAssignedIdentities" {
                # Managed Identity
                $roles = @("Managed Identity Contributor", "Managed Identity Operator")
                foreach ($role in $roles) {
                    if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName $role -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType "Managed Identity") {
                        $successCount++
                    } else {
                        $failureCount++
                    }
                }
            }
            
            default {
                # Generic contributor access for other resources
                if (Set-ResourceRole -Scope $resourceScope -RoleDefinitionName "Contributor" -ObjectId $targetUser.Id -ResourceName $resource.Name -ResourceType $resource.ResourceType) {
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
