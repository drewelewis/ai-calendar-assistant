@echo off
echo ============================================
echo CosmosDB Permissions Check
echo ============================================
echo.

echo 1. Getting current user information...
az ad signed-in-user show --query "{id:id,displayName:displayName,userPrincipalName:userPrincipalName}" --output table
if %errorlevel% neq 0 (
    echo ❌ Failed to get current user. Please run 'az login'
    pause
    exit /b 1
)

echo.
echo 2. Checking CosmosDB account access...
az cosmosdb show --name ai-calendar-assistant-cosmosdb --resource-group devops-ai-rg --query "{name:name,location:location,provisioningState:provisioningState}" --output table
if %errorlevel% neq 0 (
    echo ❌ Cannot access CosmosDB account. Check control plane permissions.
) else (
    echo ✅ CosmosDB account accessible
)

echo.
echo 3. Checking SQL databases...
az cosmosdb sql database list --account-name ai-calendar-assistant-cosmosdb --resource-group devops-ai-rg --query "[].{Name:id}" --output table
if %errorlevel% neq 0 (
    echo ❌ Cannot list databases. Check control plane permissions.
) else (
    echo ✅ Can list databases
)

echo.
echo 4. Checking SQL containers...
az cosmosdb sql container list --account-name ai-calendar-assistant-cosmosdb --resource-group devops-ai-rg --database-name CalendarAssistant --query "[].{Name:id}" --output table
if %errorlevel% neq 0 (
    echo ❌ Cannot list containers. Check control plane permissions.
) else (
    echo ✅ Can list containers
)

echo.
echo 5. Checking current RBAC assignments...
echo Data Plane Role Assignments:
az cosmosdb sql role assignment list --account-name ai-calendar-assistant-cosmosdb --resource-group devops-ai-rg --output table
if %errorlevel% neq 0 (
    echo ❌ Cannot list role assignments
)

echo.
echo Control Plane Role Assignments:
az role assignment list --scope "/subscriptions/d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e/resourceGroups/devops-ai-rg/providers/Microsoft.DocumentDB/databaseAccounts/ai-calendar-assistant-cosmosdb" --output table
if %errorlevel% neq 0 (
    echo ❌ Cannot list control plane role assignments
)

echo.
echo ============================================
echo Permission Check Complete
echo ============================================
echo.
echo The ID you mentioned (69149650-b87e-44cf-9413-db5c1a5b6d3f) 
echo is your CHAT_SESSION_ID, not a user/service principal ID.
echo.
echo Your actual identities that need permissions are:
echo - Current User ID: (shown above)
echo - Service Principal: 67891fdb-7b0b-481b-be71-fd5cb5cf9771
echo - Managed Identity: 5238e629-da2f-4bb0-aea5-14d45526c864
echo.
echo Required Data Plane Role: "Cosmos DB Built-in Data Contributor"
echo Required Control Plane Role: "Cosmos DB Account Reader Role" or "Contributor"
echo.
pause
