@echo off
REM Script to assign Cosmos DB management plane permissions to Azure Managed Identity
REM This script assigns the DocumentDB Account Contributor role for metadata operations

echo ================================================
echo Assigning Cosmos DB Management Plane permissions to Managed Identity
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

echo ================================================
echo Assigning DocumentDB Account Contributor role...
echo ================================================

az role assignment create ^
    --assignee "%AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%" ^
    --role "DocumentDB Account Contributor" ^
    --scope "%COSMOS_RESOURCE_ID%" ^
    --subscription "%SUBSCRIPTION_ID%"

if errorlevel 1 (
    echo WARNING: Failed to assign DocumentDB Account Contributor role
    echo This might be because the role is already assigned
) else (
    echo SUCCESS: DocumentDB Account Contributor role assigned successfully
)

echo.
echo ================================================
echo Verifying role assignments...
echo ================================================

echo Listing current role assignments for the Managed Identity:
az role assignment list ^
    --assignee "%AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID%" ^
    --scope "%COSMOS_RESOURCE_ID%" ^
    --output table

echo.
echo ================================================
echo Management plane role assignment process completed!
echo ================================================
echo.
echo IMPORTANT NOTES:
echo 1. Role assignments may take a few minutes to propagate
echo 2. The DocumentDB Account Contributor role allows management operations like:
echo    - Reading database metadata (readMetadata)
echo    - Managing databases and containers
echo    - Configuring account settings
echo 3. This is a management plane permission for Azure Resource Manager
echo 4. Your application should use the Managed Identity for authentication
echo 5. You also need data plane permissions for actual data access
echo.
echo Next steps:
echo 1. Run the data plane permissions script: _cosmosdb_assign_managed_identity_data_plane_permissions.bat
echo 2. Wait 5-10 minutes for all permissions to propagate
echo 3. Test the connection with the new permissions
echo 4. Monitor the application logs for any authentication issues
echo.

pause
