@echo off
echo Azure CLI Diagnostic Script
echo ========================
echo.

echo 1. Checking if Azure CLI is installed...
az --version
if %errorlevel% neq 0 (
    echo ❌ Azure CLI is not installed or not in PATH
    echo Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
    pause
    exit /b 1
)

echo.
echo 2. Checking login status (with timeout)...
timeout 10 az account show
if %errorlevel% neq 0 (
    echo.
    echo ❌ Not logged in or login expired
    echo Please run: az login
    pause
    exit /b 1
)

echo.
echo 3. Listing available subscriptions...
timeout 15 az account list --output table

echo.
echo 4. Checking current subscription...
timeout 10 az account show --query "{name:name, id:id, tenantId:tenantId}" --output table

echo.
echo ✅ Azure CLI diagnostics complete
pause
