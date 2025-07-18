# CosmosDB Permissions Quick Check
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " CosmosDB Permissions Check" -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if logged into Azure CLI
Write-Host "1. Checking Azure CLI login status..." -ForegroundColor Yellow
try {
    $currentUser = az ad signed-in-user show --query "{id:id,displayName:displayName,userPrincipalName:userPrincipalName}" | ConvertFrom-Json
    Write-Host "✅ Current User:" -ForegroundColor Green
    Write-Host "   ID: $($currentUser.id)" -ForegroundColor White
    Write-Host "   Name: $($currentUser.displayName)" -ForegroundColor White
    Write-Host "   UPN: $($currentUser.userPrincipalName)" -ForegroundColor White
    $userId = $currentUser.id
} catch {
    Write-Host "❌ Not logged into Azure CLI. Run 'az login'" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Important Clarification:" -ForegroundColor Yellow
Write-Host "   The ID you highlighted (69149650-b87e-44cf-9413-db5c1a5b6d3f)" -ForegroundColor White
Write-Host "   is your CHAT_SESSION_ID, not a user/principal ID." -ForegroundColor White
Write-Host ""
Write-Host "   Your actual identities that need CosmosDB permissions:" -ForegroundColor White
Write-Host "   • Current User: $userId" -ForegroundColor Cyan
Write-Host "   • Service Principal: 67891fdb-7b0b-481b-be71-fd5cb5cf9771" -ForegroundColor Cyan
Write-Host "   • Managed Identity: 5238e629-da2f-4bb0-aea5-14d45526c864" -ForegroundColor Cyan

Write-Host ""
Write-Host "3. Testing CosmosDB access..." -ForegroundColor Yellow

# Test CosmosDB account access
try {
    $cosmosAccount = az cosmosdb show --name "ai-calendar-assistant-cosmosdb" --resource-group "devops-ai-rg" --query "{name:name,location:location,provisioningState:provisioningState}" | ConvertFrom-Json
    Write-Host "✅ CosmosDB Account Access: SUCCESS" -ForegroundColor Green
    Write-Host "   Account: $($cosmosAccount.name)" -ForegroundColor White
    Write-Host "   Status: $($cosmosAccount.provisioningState)" -ForegroundColor White
} catch {
    Write-Host "❌ CosmosDB Account Access: FAILED" -ForegroundColor Red
    Write-Host "   Missing control plane permissions" -ForegroundColor Yellow
}

# Test database listing
Write-Host ""
try {
    $databases = az cosmosdb sql database list --account-name "ai-calendar-assistant-cosmosdb" --resource-group "devops-ai-rg" --query "[].id" -o json | ConvertFrom-Json
    Write-Host "✅ Database Listing: SUCCESS" -ForegroundColor Green
    Write-Host "   Databases: $($databases -join ', ')" -ForegroundColor White
} catch {
    Write-Host "❌ Database Listing: FAILED" -ForegroundColor Red
}

# Test container listing
Write-Host ""
try {
    $containers = az cosmosdb sql container list --account-name "ai-calendar-assistant-cosmosdb" --resource-group "devops-ai-rg" --database-name "CalendarAssistant" --query "[].id" -o json | ConvertFrom-Json
    Write-Host "✅ Container Listing: SUCCESS" -ForegroundColor Green
    Write-Host "   Containers: $($containers -join ', ')" -ForegroundColor White
} catch {
    Write-Host "❌ Container Listing: FAILED" -ForegroundColor Red
}

# Check RBAC assignments
Write-Host ""
Write-Host "4. Checking RBAC assignments..." -ForegroundColor Yellow
try {
    $roleAssignments = az cosmosdb sql role assignment list --account-name "ai-calendar-assistant-cosmosdb" --resource-group "devops-ai-rg" -o json | ConvertFrom-Json
    if ($roleAssignments.Count -gt 0) {
        Write-Host "✅ Data Plane Role Assignments Found: $($roleAssignments.Count)" -ForegroundColor Green
        foreach ($assignment in $roleAssignments) {
            Write-Host "   • Principal: $($assignment.principalId)" -ForegroundColor White
            Write-Host "     Role: $($assignment.roleDefinitionId)" -ForegroundColor White
            Write-Host "     Scope: $($assignment.scope)" -ForegroundColor White
            Write-Host ""
        }
    } else {
        Write-Host "❌ No Data Plane Role Assignments Found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Cannot check role assignments" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "🔹 To grant Data Plane permissions (application data access):" -ForegroundColor Yellow
Write-Host "   az cosmosdb sql role assignment create \\" -ForegroundColor White
Write-Host "     --account-name ai-calendar-assistant-cosmosdb \\" -ForegroundColor White  
Write-Host "     --resource-group devops-ai-rg \\" -ForegroundColor White
Write-Host "     --scope `"/`" \\" -ForegroundColor White
Write-Host "     --principal-id $userId \\" -ForegroundColor Cyan
Write-Host "     --role-definition-name `"Cosmos DB Built-in Data Contributor`"" -ForegroundColor White

Write-Host ""
Write-Host "🔹 To grant Control Plane permissions (account management):" -ForegroundColor Yellow
Write-Host "   az role assignment create \\" -ForegroundColor White
Write-Host "     --assignee $userId \\" -ForegroundColor Cyan
Write-Host "     --role `"Cosmos DB Account Reader Role`" \\" -ForegroundColor White
Write-Host "     --scope `"/subscriptions/d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e/resourceGroups/devops-ai-rg/providers/Microsoft.DocumentDB/databaseAccounts/ai-calendar-assistant-cosmosdb`"" -ForegroundColor White

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
