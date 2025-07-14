@echo off
echo Setting up CosmosDB RBAC permissions...
echo.

REM CosmosDB account details from error message
set COSMOS_ACCOUNT=ai-calendar-assistant-cosmosdb
set USER_OBJECT_ID=69149650-b87e-44cf-9413-db5c1a5b6d3f

echo CosmosDB account: %COSMOS_ACCOUNT%
echo Your user object ID: %USER_OBJECT_ID%
echo.

echo Please provide the resource group name for your CosmosDB account.
echo You can find this in the Azure Portal under your CosmosDB account details.
echo.
set /p RESOURCE_GROUP="Enter resource group name: "

if "%RESOURCE_GROUP%"=="" (
    echo Error: Resource group name cannot be empty.
    pause
    exit /b 1
)

echo.
echo Using resource group: %RESOURCE_GROUP%
echo.

REM Verify the CosmosDB account exists in this resource group
echo Verifying CosmosDB account exists...
az cosmosdb show --name %COSMOS_ACCOUNT% --resource-group %RESOURCE_GROUP% --query name --output tsv >nul 2>&1

if %ERRORLEVEL% neq 0 (
    echo Error: CosmosDB account '%COSMOS_ACCOUNT%' not found in resource group '%RESOURCE_GROUP%'
    echo Please check the resource group name and try again.
    pause
    exit /b 1
)

echo ✓ CosmosDB account found!
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
    echo This could be because:
    echo 1. You don't have sufficient permissions on the subscription
    echo 2. The role assignment already exists
    echo 3. The resource group or account name is incorrect
    echo.
    echo Please check the error message above for details.
)

echo.
pause
