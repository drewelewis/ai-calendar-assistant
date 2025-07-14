@echo off
echo CosmosDB Firewall Management Script
echo ====================================
echo.

REM CosmosDB account details
set COSMOS_ACCOUNT=ai-calendar-assistant-cosmosdb
set RESOURCE_GROUP=devops-ai-rg

echo Getting your current public IP address...
for /f "tokens=*" %%i in ('curl -s https://api.ipify.org') do set CURRENT_IP=%%i
echo Your current IP: %CURRENT_IP%
echo.

echo Current CosmosDB firewall rules:
az cosmosdb show --name %COSMOS_ACCOUNT% --resource-group %RESOURCE_GROUP% --query "ipRules[].ipAddressOrRange" --output table
echo.

echo Choose an option:
echo 1. Add current IP to firewall
echo 2. Enable access from all Azure services
echo 3. Enable access from Azure Portal
echo 4. Show current firewall rules
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Adding your current IP (%CURRENT_IP%) to CosmosDB firewall...
    az cosmosdb update --name %COSMOS_ACCOUNT% --resource-group %RESOURCE_GROUP% --ip-range-filter "%CURRENT_IP%"
    echo ✓ IP address added successfully!
) else if "%choice%"=="2" (
    echo Enabling access from all Azure services...
    az cosmosdb update --name %COSMOS_ACCOUNT% --resource-group %RESOURCE_GROUP% --enable-virtual-network true
    echo ✓ Azure services access enabled!
) else if "%choice%"=="3" (
    echo Enabling access from Azure Portal...
    az cosmosdb update --name %COSMOS_ACCOUNT% --resource-group %RESOURCE_GROUP% --ip-range-filter "0.0.0.0"
    echo ✓ Azure Portal access enabled!
) else if "%choice%"=="4" (
    echo Current firewall rules:
    az cosmosdb show --name %COSMOS_ACCOUNT% --resource-group %RESOURCE_GROUP% --query "{ipRules: ipRules, isVirtualNetworkFilterEnabled: isVirtualNetworkFilterEnabled}" --output table
) else if "%choice%"=="5" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo Testing connection...
python _cosmosdb_test_auth.py

pause
