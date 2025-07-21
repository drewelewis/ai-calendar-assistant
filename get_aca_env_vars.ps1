#!/usr/bin/env pwsh
# PowerShell script to get Azure Container App environment variables

Write-Host "🔍 Getting Azure Container App Environment Variables" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Get the container app configuration
Write-Host "`n📋 Retrieving container app configuration..." -ForegroundColor Yellow

try {
    $containerApp = az containerapp show --name aiwrapper --resource-group devops-ai-rg | ConvertFrom-Json
    
    if ($containerApp) {
        Write-Host "✅ Container app found" -ForegroundColor Green
        
        # Extract environment variables
        $envVars = $containerApp.properties.template.containers[0].env
        
        if ($envVars) {
            Write-Host "`n📊 Environment Variables:" -ForegroundColor Yellow
            Write-Host "=========================" -ForegroundColor Yellow
            
            # Sort by name for easier reading
            $sortedEnvVars = $envVars | Sort-Object name
            
            foreach ($envVar in $sortedEnvVars) {
                $name = $envVar.name
                $value = $envVar.value
                
                # Mask sensitive values but show Azure Maps specific ones
                if ($name -like "*KEY*" -or $name -like "*SECRET*" -or $name -like "*PASSWORD*" -or $name -like "*TOKEN*") {
                    if ($name -eq "AZURE_MAPS_SUBSCRIPTION_KEY") {
                        if ($value) {
                            Write-Host "   ⚠️  $name = [PRESENT - SHOULD BE REMOVED]" -ForegroundColor Red
                        } else {
                            Write-Host "   ✅ $name = [NOT SET - GOOD]" -ForegroundColor Green
                        }
                    } else {
                        $maskedValue = if ($value) { "[MASKED]" } else { "[NOT SET]" }
                        Write-Host "   🔒 $name = $maskedValue" -ForegroundColor Gray
                    }
                } elseif ($name -like "*AZURE_MAPS*") {
                    Write-Host "   🗺️  $name = $value" -ForegroundColor Cyan
                } else {
                    # Show first 50 chars for other variables
                    $displayValue = if ($value -and $value.Length -gt 50) { 
                        $value.Substring(0, 50) + "..." 
                    } else { 
                        $value 
                    }
                    Write-Host "   📝 $name = $displayValue" -ForegroundColor White
                }
            }
            
            # Specifically check for Azure Maps variables
            Write-Host "`n🗺️ Azure Maps Configuration Check:" -ForegroundColor Yellow
            Write-Host "===================================" -ForegroundColor Yellow
            
            $azureMapsVars = $envVars | Where-Object { $_.name -like "*AZURE_MAPS*" }
            
            if ($azureMapsVars) {
                foreach ($var in $azureMapsVars) {
                    $status = if ($var.value) { "✅ SET" } else { "❌ NOT SET" }
                    Write-Host "   $($var.name): $status" -ForegroundColor $(if ($var.value) { "Green" } else { "Red" })
                    
                    if ($var.name -eq "AZURE_MAPS_SUBSCRIPTION_KEY" -and $var.value) {
                        Write-Host "   ⚠️  WARNING: Subscription key is set - this will override managed identity!" -ForegroundColor Red
                        Write-Host "   💡 Remove this environment variable to use managed identity" -ForegroundColor Yellow
                    }
                }
            } else {
                Write-Host "   ❌ No Azure Maps environment variables found" -ForegroundColor Red
            }
            
            # Check for managed identity related variables
            Write-Host "`n🔐 Managed Identity Check:" -ForegroundColor Yellow
            Write-Host "===========================" -ForegroundColor Yellow
            
            $identityVars = @("MSI_ENDPOINT", "IDENTITY_ENDPOINT", "IDENTITY_HEADER", "AZURE_CLIENT_ID")
            
            foreach ($varName in $identityVars) {
                $var = $envVars | Where-Object { $_.name -eq $varName }
                $status = if ($var -and $var.value) { "✅ SET" } else { "❌ NOT SET" }
                $color = if ($var -and $var.value) { "Green" } else { "Red" }
                Write-Host "   ${varName}: $status" -ForegroundColor $color
            }
            
        } else {
            Write-Host "❌ No environment variables found" -ForegroundColor Red
        }
        
    } else {
        Write-Host "❌ Container app not found" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error retrieving container app: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Make sure you're authenticated with Azure CLI: az login" -ForegroundColor Yellow
}

Write-Host "`n🔍 Analysis complete!" -ForegroundColor Cyan
