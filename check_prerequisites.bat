@echo off
echo ==========================================
echo Azure Container Registry - Diagnostic Tool
echo ==========================================
echo.

echo 1. Checking if Docker is installed...
where docker >nul 2>&1
if errorlevel 1 (
    echo   FAIL: Docker not found in PATH
    goto :end
) else (
    echo   OK: Docker found in PATH
)

echo.
echo 2. Checking if Docker is running...
docker version --format "{{.Server.Version}}" >nul 2>&1
if errorlevel 1 (
    echo   FAIL: Docker is not running - please start Docker Desktop
    goto :end
) else (
    echo   OK: Docker is running
)

echo.
echo 3. Checking if Azure CLI is installed...
where az >nul 2>&1
if errorlevel 1 (
    echo   FAIL: Azure CLI not found in PATH
    echo   Please install from: https://aka.ms/installazurecli
    goto :end
) else (
    echo   OK: Azure CLI found in PATH
)

echo.
echo 4. Testing Azure CLI basic command...
az --version >nul 2>&1
if errorlevel 1 (
    echo   FAIL: Azure CLI not working properly
    goto :end
) else (
    echo   OK: Azure CLI is working
)

echo.
echo 5. Checking Azure login status...
az account show --output none 2>nul
if errorlevel 1 (
    echo   INFO: Not logged into Azure (this is normal if first time)
) else (
    echo   OK: Already logged into Azure
    echo   Current account:
    az account show --query "[name,user.name]" --output table
)

echo.
echo ==========================================
echo Diagnostic complete!
echo ==========================================
echo.
echo If all checks passed, you can run the main deployment script.
echo If any failed, please fix the issues above first.

:end
echo.
pause
