@echo off
echo ================================================================
echo 🔍 Getting Azure Container App Environment Variables
echo ================================================================
echo.

echo 📋 Retrieving container app configuration...
echo.

REM Get all environment variables and save to temp file
az containerapp show --name aiwrapper --resource-group devops-ai-rg --query "properties.template.containers[0].env[*].{Name:name,Value:value}" --output json > temp_env.json

if %ERRORLEVEL% EQU 0 (
    echo ✅ Successfully retrieved environment variables
    echo.
    echo 📊 Environment Variables:
    echo =========================
    
    REM Display the JSON content
    type temp_env.json
    
    echo.
    echo 🗺️ Checking for Azure Maps Subscription Key...
    echo =============================================
    
    REM Check if Azure Maps subscription key exists
    findstr /i "AZURE_MAPS_SUBSCRIPTION_KEY" temp_env.json >nul
    if %ERRORLEVEL% EQU 0 (
        echo ⚠️  WARNING: AZURE_MAPS_SUBSCRIPTION_KEY found in environment!
        echo 💡 This will override managed identity authentication
        echo 🔧 Remove this environment variable to use managed identity
    ) else (
        echo ✅ AZURE_MAPS_SUBSCRIPTION_KEY not found - good for managed identity!
    )
    
    echo.
    echo 🔐 Checking for Managed Identity variables...
    echo ============================================
    
    findstr /i "AZURE_MAPS_CLIENT_ID" temp_env.json >nul
    if %ERRORLEVEL% EQU 0 (
        echo ✅ AZURE_MAPS_CLIENT_ID found
    ) else (
        echo ❌ AZURE_MAPS_CLIENT_ID not found
    )
    
    findstr /i "AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID" temp_env.json >nul
    if %ERRORLEVEL% EQU 0 (
        echo ✅ AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID found
    ) else (
        echo ❌ AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID not found
    )
    
    REM Clean up temp file
    del temp_env.json >nul 2>&1
    
) else (
    echo ❌ Failed to retrieve environment variables
    echo 💡 Make sure you're authenticated with Azure CLI: az login
)

echo.
echo 🔍 Analysis complete!
pause
