@echo off
echo Setting up CosmosDB RBAC permissions...
echo.

REM Get current user's object ID
echo Getting your user object ID...
for /f "tokens=*" %%i in ('az ad signed-in-user show --query id --output tsv') do set USER_OBJECT_ID=%%i
echo Your user object ID: %USER_OBJECT_ID%
echo.

REM CosmosDB account details from error message
set COSMOS_ACCOUNT=ai-calendar-assistant-cosmosdb
echo CosmosDB account: %COSMOS_ACCOUNT%

REM Find the resource group for this CosmosDB account
echo Finding resource group for CosmosDB account...
for /f "tokens=*" %%i in ('az cosmosdb show --name %COSMOS_ACCOUNT% --query resourceGroup --output tsv') do set RESOURCE_GROUP=%%i
echo Resource group: %RESOURCE_GROUP%
echo.

REM Assign Cosmos DB Built-in Data Contributor role
echo Assigning Cosmos DB Built-in Data Contributor role...
az cosmosdb sql role assignment create ^
  --account-name %COSMOS_ACCOUNT% ^
  --resource-group %RESOURCE_GROUP% ^
  --scope "/" ^
  --principal-id %USER_OBJECT_ID% ^
  --role-definition-id 87a39d53-fc1b-424a-814c-f7e04687dc9e

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✓ RBAC permissions assigned successfully!
    echo.
    echo Testing the connection...
    python _cosmosdb_test_auth.py
) else (
    echo.
    echo ❌ Failed to assign RBAC permissions.
    echo Please check that you have sufficient permissions on the subscription.
    echo You may need to contact your Azure administrator.
)

echo.
pause
