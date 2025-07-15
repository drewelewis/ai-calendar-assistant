@echo off
REM Script to assign Cosmos DB permissions to Azure Managed Identity
REM This script assigns both Cosmos DB Built-in Data Reader and Data Contributor roles

echo ================================================
echo Assigning Cosmos DB permissions to Managed Identity
echo ================================================

az login

REM Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env file...
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%b"=="" (
            set "%%a=%%b"
        )
    )
) else (
    echo .env file not found. Please ensure the .env file exists.
    exit /b 1
)

REM Validate required environment variables
if "%AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%"=="" (
    echo ERROR: AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID not found in environment variables
    exit /b 1
)

if "%AZURE_COSMOSDB_ACCOUNT%"=="" (
    echo ERROR: AZURE_COSMOSDB_ACCOUNT not found in environment variables
    exit /b 1
)

if "%AZURE_RESOURCE_GROUP%"=="" (
    echo ERROR: AZURE_RESOURCE_GROUP not found in environment variables
    exit /b 1
)

echo.
echo Configuration:
echo - Managed Identity ID: %AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%
echo - Cosmos DB Account: %AZURE_COSMOSDB_ACCOUNT%
echo - Resource Group: %AZURE_RESOURCE_GROUP%
echo.

REM Check if Azure CLI is installed and user is logged in
echo Checking Azure CLI authentication...
az account show >nul 2>&1
if errorlevel 1 (
    echo ERROR: Azure CLI is not installed or you are not logged in.
    echo Please install Azure CLI and run 'az login' first.
    exit /b 1
)

echo Azure CLI authentication verified.
echo.

REM Get the current subscription ID
for /f "tokens=*" %%i in ('az account show --query "id" -o tsv') do set SUBSCRIPTION_ID=%%i
echo Current subscription: %SUBSCRIPTION_ID%

REM Construct the Cosmos DB account resource ID
set COSMOS_RESOURCE_ID=/subscriptions/%SUBSCRIPTION_ID%/resourceGroups/%AZURE_RESOURCE_GROUP%/providers/Microsoft.DocumentDB/databaseAccounts/%AZURE_COSMOSDB_ACCOUNT%

echo.
echo Cosmos DB Resource ID: %COSMOS_RESOURCE_ID%
echo.

REM Cosmos DB Built-in Data Reader role definition ID
set COSMOS_DATA_READER_ROLE=00000000-0000-0000-0000-000000000001

REM Cosmos DB Built-in Data Contributor role definition ID
set COSMOS_DATA_CONTRIBUTOR_ROLE=00000000-0000-0000-0000-000000000002

echo ================================================
echo Assigning Cosmos DB Built-in Data Reader role...
echo ================================================

az cosmosdb sql role assignment create ^
    --account-name "%AZURE_COSMOSDB_ACCOUNT%" ^
    --resource-group "%AZURE_RESOURCE_GROUP%" ^
    --scope "%COSMOS_RESOURCE_ID%" ^
    --principal-id "%AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%" ^
    --role-definition-id "%COSMOS_DATA_READER_ROLE%"

if errorlevel 1 (
    echo WARNING: Failed to assign Cosmos DB Built-in Data Reader role
    echo This might be because the role is already assigned
) else (
    echo SUCCESS: Cosmos DB Built-in Data Reader role assigned successfully
)

echo.
echo ================================================
echo Assigning Cosmos DB Built-in Data Contributor role...
echo ================================================

az cosmosdb sql role assignment create ^
    --account-name "%AZURE_COSMOSDB_ACCOUNT%" ^
    --resource-group "%AZURE_RESOURCE_GROUP%" ^
    --scope "%COSMOS_RESOURCE_ID%" ^
    --principal-id "%AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%" ^
    --role-definition-id "%COSMOS_DATA_CONTRIBUTOR_ROLE%"

if errorlevel 1 (
    echo WARNING: Failed to assign Cosmos DB Built-in Data Contributor role
    echo This might be because the role is already assigned
) else (
    echo SUCCESS: Cosmos DB Built-in Data Contributor role assigned successfully
)

echo.
echo ================================================
echo Verifying role assignments...
echo ================================================

echo Listing current role assignments for the Managed Identity:
az cosmosdb sql role assignment list ^
    --account-name "%AZURE_COSMOSDB_ACCOUNT%" ^
    --resource-group "%AZURE_RESOURCE_GROUP%" ^
    --query "[?principalId=='%AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%']" ^
    --output table

echo.
echo ================================================
echo Role assignment process completed!
echo ================================================
echo.
echo IMPORTANT NOTES:
echo 1. Role assignments may take a few minutes to propagate
echo 2. The Data Reader role allows read access to all data
echo 3. The Data Contributor role allows read/write access to all data
echo 4. These are data plane permissions for Cosmos DB RBAC
echo 5. Your application should use the Managed Identity for authentication
echo.
echo Next steps:
echo 1. Update your application to use Managed Identity authentication
echo 2. Test the connection with the new permissions
echo 3. Monitor the application logs for any authentication issues
echo.

pause
