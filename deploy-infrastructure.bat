@echo off
REM AI Calendar Assistant - Azure Infrastructure Deployment Script
REM This script deploys the complete infrastructure using Azure Developer CLI (azd)

echo ====================================================================
echo AI Calendar Assistant - Infrastructure Deployment
echo ====================================================================
echo.

REM Check if azd is installed
azd version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Azure Developer CLI (azd) is not installed or not in PATH
    echo Please install it from: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd
    echo.
    pause
    exit /b 1
)

echo ✅ Azure Developer CLI detected
echo.

REM Check if user is logged in to Azure
az account show >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 Please log in to Azure...
    az login
    if %errorlevel% neq 0 (
        echo ❌ Azure login failed
        pause
        exit /b 1
    )
)

echo ✅ Azure CLI authentication verified
echo.

REM Initialize azd if needed
if not exist ".azure" (
    echo 🚀 Initializing Azure Developer CLI environment...
    azd init --template . --no-prompt
    if %errorlevel% neq 0 (
        echo ❌ azd init failed
        pause
        exit /b 1
    )
    echo ✅ azd initialized successfully
    echo.
)

REM Check for required environment variables
echo 🔍 Checking required environment variables...

set "missing_vars="

if "%ENTRA_GRAPH_APPLICATION_CLIENT_ID%"=="" set "missing_vars=%missing_vars% ENTRA_GRAPH_APPLICATION_CLIENT_ID"
if "%ENTRA_GRAPH_APPLICATION_CLIENT_SECRET%"=="" set "missing_vars=%missing_vars% ENTRA_GRAPH_APPLICATION_CLIENT_SECRET"
if "%ENTRA_GRAPH_APPLICATION_TENANT_ID%"=="" set "missing_vars=%missing_vars% ENTRA_GRAPH_APPLICATION_TENANT_ID"

if not "%missing_vars%"=="" (
    echo ❌ Missing required environment variables:%missing_vars%
    echo.
    echo Please ensure your .env file contains:
    echo   ENTRA_GRAPH_APPLICATION_CLIENT_ID=your-client-id
    echo   ENTRA_GRAPH_APPLICATION_CLIENT_SECRET=your-client-secret
    echo   ENTRA_GRAPH_APPLICATION_TENANT_ID=your-tenant-id
    echo.
    echo You can set these by running:
    echo   azd env set ENTRA_GRAPH_APPLICATION_CLIENT_ID "your-value"
    echo   azd env set ENTRA_GRAPH_APPLICATION_CLIENT_SECRET "your-value"
    echo   azd env set ENTRA_GRAPH_APPLICATION_TENANT_ID "your-value"
    echo.
    pause
    exit /b 1
)

echo ✅ Environment variables verified
echo.

REM Set default values if not provided
if "%OPENAI_MODEL_DEPLOYMENT_NAME%"=="" (
    echo 🔧 Setting default OPENAI_MODEL_DEPLOYMENT_NAME to 'gpt-4o'
    azd env set OPENAI_MODEL_DEPLOYMENT_NAME "gpt-4o"
)

if "%OPENAI_MODEL_NAME%"=="" (
    echo 🔧 Setting default OPENAI_MODEL_NAME to 'gpt-4o'
    azd env set OPENAI_MODEL_NAME "gpt-4o"
)

if "%OPENAI_MODEL_VERSION%"=="" (
    echo 🔧 Setting default OPENAI_MODEL_VERSION to '2024-08-06'
    azd env set OPENAI_MODEL_VERSION "2024-08-06"
)

if "%COSMOS_DATABASE%"=="" (
    echo 🔧 Setting default COSMOS_DATABASE to 'CalendarAssistant'
    azd env set COSMOS_DATABASE "CalendarAssistant"
)

if "%COSMOS_CONTAINER%"=="" (
    echo 🔧 Setting default COSMOS_CONTAINER to 'ChatHistory'
    azd env set COSMOS_CONTAINER "ChatHistory"
)

echo.

REM Preview deployment
echo 📋 Previewing infrastructure deployment...
azd provision --preview
if %errorlevel% neq 0 (
    echo ❌ Deployment preview failed
    pause
    exit /b 1
)

echo.
echo 🔍 Deployment preview completed. Review the changes above.
echo.
set /p "confirm=Do you want to proceed with the deployment? (y/N): "
if /i not "%confirm%"=="y" (
    echo 🛑 Deployment cancelled by user
    pause
    exit /b 0
)

echo.
echo 🚀 Starting infrastructure deployment...
echo This may take 10-15 minutes...
echo.

REM Deploy infrastructure and application
azd up --no-prompt
if %errorlevel% neq 0 (
    echo ❌ Deployment failed
    echo.
    echo 🔍 You can check the logs with:
    echo   azd logs
    echo.
    echo 🔄 To retry deployment:
    echo   azd up
    echo.
    pause
    exit /b 1
)

echo.
echo 🎉 Deployment completed successfully!
echo.
echo 📊 Resource Information:
azd show --output table

echo.
echo 🌐 Application URLs:
azd env get-values | findstr "AZURE_CONTAINER_APP_ENDPOINT"

echo.
echo 📋 Next Steps:
echo   1. Test the application health endpoint
echo   2. Configure Microsoft Graph API permissions if needed
echo   3. Monitor the application in Azure Application Insights
echo   4. View logs with: azd logs
echo.

pause
