@echo off
echo Setting up Application Insights for AI Calendar Assistant...
echo.

REM Check if Azure CLI is available and logged in
echo Checking Azure CLI login status...
timeout 15 az account show >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Azure CLI is not logged in or not responding
    echo Please run: az login
    echo Then set your subscription: az account set --subscription "your-subscription-id"
    pause
    exit /b 1
)

echo ✅ Azure CLI is working

REM Prompt for resource group if not provided
if "%1"=="" (
    set /p RESOURCE_GROUP="Enter your Azure Resource Group name: "
) else (
    set RESOURCE_GROUP=%1
)

if "%RESOURCE_GROUP%"=="" (
    echo Error: Resource group name is required
    pause
    exit /b 1
)

echo Resource Group: %RESOURCE_GROUP%
echo.

REM Set Application Insights name
set APP_INSIGHTS_NAME=ai-calendar-assistant-insights

REM Check if resource group exists first
echo Checking if resource group exists...
timeout 15 az group show --name %RESOURCE_GROUP% >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Resource group '%RESOURCE_GROUP%' does not exist or is not accessible
    echo Please create it first: az group create --name %RESOURCE_GROUP% --location eastus
    pause
    exit /b 1
)

echo ✅ Resource group exists

REM Check if Application Insights already exists
echo Checking if Application Insights instance exists...
timeout 30 az monitor app-insights component show --app %APP_INSIGHTS_NAME% --resource-group %RESOURCE_GROUP% >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Application Insights instance '%APP_INSIGHTS_NAME%' already exists
    goto :get_connection_string
)

echo Creating Application Insights instance...
timeout 60 az monitor app-insights component create ^
    --app %APP_INSIGHTS_NAME% ^
    --location "eastus" ^
    --resource-group %RESOURCE_GROUP% ^
    --application-type web ^
    --tags "project=ai-calendar-assistant" "environment=development"

if %errorlevel% neq 0 (
    echo ❌ Failed to create Application Insights instance
    echo This could be due to:
    echo - Insufficient permissions
    echo - Resource group doesn't exist
    echo - Network connectivity issues
    echo - Azure CLI timeout
    pause
    exit /b 1
)

echo ✅ Application Insights instance created successfully

:get_connection_string
echo.
echo Getting connection string...
timeout 30 az monitor app-insights component show ^
    --app %APP_INSIGHTS_NAME% ^
    --resource-group %RESOURCE_GROUP% ^
    --query "connectionString" ^
    --output tsv > temp_connection.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to get connection string
    pause
    exit /b 1
)

set /p CONNECTION_STRING=<temp_connection.txt
del temp_connection.txt

if "%CONNECTION_STRING%"=="" (
    echo ❌ Connection string is empty
    pause
    exit /b 1
)

echo ✅ Connection string retrieved

REM Create or update .env file
echo.
echo Updating .env file...
if exist .env (
    REM Remove existing connection string line if it exists
    findstr /v "APPLICATIONINSIGHTS_CONNECTION_STRING" .env > temp_env.txt
    move temp_env.txt .env
)

echo APPLICATIONINSIGHTS_CONNECTION_STRING=%CONNECTION_STRING% >> .env

echo ✅ .env file updated with connection string
echo.
echo 🎉 Application Insights setup complete!
echo.
echo Connection string has been added to your .env file.
echo You can now run your application with telemetry enabled.
echo.
pause
