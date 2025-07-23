@echo off
REM AI Calendar Assistant - Admin Access Configuration using Azure CLI
REM This script grants administrative permissions to specified users

echo.
echo =================================================================
echo AI Calendar Assistant - Admin Access Configuration (Azure CLI)
echo =================================================================
echo.
echo User: rapenmetsa@MngEnvMCAP623732.onmicrosoft.com
echo Subscription ID: d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e
echo Resource Group: devops-ai-rg
echo.

REM Check if Azure CLI is installed
az --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Azure CLI is not installed or not in PATH.
    echo Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
    pause
    exit /b 1
)

REM Check if user is logged in
az account show >nul 2>&1
if errorlevel 1 (
    echo You are not logged in to Azure. Please login...
    az login
    if errorlevel 1 (
        echo ERROR: Failed to login to Azure
        pause
        exit /b 1
    )
)

REM Set subscription
echo Setting subscription context...
az account set --subscription "d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e"
if errorlevel 1 (
    echo ERROR: Failed to set subscription context
    pause
    exit /b 1
)

echo.
echo Configuring admin access...
echo.

REM Get the user object ID
echo Getting user information...
for /f "tokens=*" %%i in ('az ad user show --id "rapenmetsa@MngEnvMCAP623732.onmicrosoft.com" --query "id" --output tsv 2^>nul') do set USER_OBJECT_ID=%%i

if "%USER_OBJECT_ID%"=="" (
    echo ERROR: Could not find user rapenmetsa@MngEnvMCAP623732.onmicrosoft.com
    echo Please verify the email address is correct
    pause
    exit /b 1
)

echo Found user with Object ID: %USER_OBJECT_ID%
echo.

REM Get resource group ID
for /f "tokens=*" %%i in ('az group show --name "devops-ai-rg" --query "id" --output tsv 2^>nul') do set RG_ID=%%i

if "%RG_ID%"=="" (
    echo ERROR: Could not find resource group devops-ai-rg
    pause
    exit /b 1
)

echo Found resource group: %RG_ID%
echo.

REM Assign Contributor role at resource group level
echo Assigning Contributor role at resource group level...
az role assignment create --assignee %USER_OBJECT_ID% --role "Contributor" --scope %RG_ID%
if errorlevel 1 (
    echo WARNING: Failed to assign Contributor role at resource group level
) else (
    echo SUCCESS: Assigned Contributor role at resource group level
)

REM Get all resources in the resource group
echo.
echo Getting resources in the resource group...
for /f "tokens=*" %%i in ('az resource list --resource-group "devops-ai-rg" --query "[].{id:id,type:type,name:name}" --output tsv') do (
    set "line=%%i"
    call :process_resource
)

echo.
echo =================================================================
echo Admin access configuration completed!
echo.
echo The user rapenmetsa@MngEnvMCAP623732.onmicrosoft.com now has:
echo - Contributor access to the resource group devops-ai-rg
echo - Specific role assignments on individual resources
echo.
echo Next steps for the admin user:
echo 1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
echo 2. Login: az login
echo 3. Set subscription: az account set --subscription d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e
echo 4. Access Azure Portal: https://portal.azure.com
echo =================================================================
pause
exit /b 0

:process_resource
for /f "tokens=1,2,3 delims=	" %%a in ("%line%") do (
    set RESOURCE_ID=%%a
    set RESOURCE_TYPE=%%b
    set RESOURCE_NAME=%%c
    
    echo Processing: !RESOURCE_NAME! ^(!RESOURCE_TYPE!^)
    
    REM Assign specific roles based on resource type
    if "!RESOURCE_TYPE!"=="Microsoft.DocumentDB/databaseAccounts" (
        echo   Assigning DocumentDB Account Contributor role...
        az role assignment create --assignee %USER_OBJECT_ID% --role "DocumentDB Account Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
        az role assignment create --assignee %USER_OBJECT_ID% --role "Cosmos DB Account Reader Role" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.App/containerApps" (
        echo   Assigning Container App roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.CognitiveServices/accounts" (
        echo   Assigning Cognitive Services roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Cognitive Services OpenAI Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
        az role assignment create --assignee %USER_OBJECT_ID% --role "Cognitive Services User" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.Insights/components" (
        echo   Assigning Application Insights roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Application Insights Component Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
        az role assignment create --assignee %USER_OBJECT_ID% --role "Monitoring Reader" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.OperationalInsights/workspaces" (
        echo   Assigning Log Analytics roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Log Analytics Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
        az role assignment create --assignee %USER_OBJECT_ID% --role "Log Analytics Reader" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.Maps/accounts" (
        echo   Assigning Azure Maps roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.Cache/Redis" (
        echo   Assigning Redis Cache roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Redis Cache Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.BotService/botServices" (
        echo   Assigning Bot Service roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
    )
    
    if "!RESOURCE_TYPE!"=="Microsoft.ManagedIdentity/userAssignedIdentities" (
        echo   Assigning Managed Identity roles...
        az role assignment create --assignee %USER_OBJECT_ID% --role "Managed Identity Contributor" --scope "!RESOURCE_ID!" >nul 2>&1
        az role assignment create --assignee %USER_OBJECT_ID% --role "Managed Identity Operator" --scope "!RESOURCE_ID!" >nul 2>&1
    )
)
goto :eof
