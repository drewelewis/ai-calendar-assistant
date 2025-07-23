@echo off
echo Configuring admin access for AI Calendar Assistant...
echo.
echo User: rapenmetsa@MngEnvMCAP623732.onmicrosoft.com
echo Subscription ID: d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e  
echo Resource Group: devops-ai-rg
echo.

REM Check if PowerShell is available
powershell -Command "Get-ExecutionPolicy" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell is not available or accessible.
    pause
    exit /b 1
)

echo Running PowerShell script...
powershell -ExecutionPolicy Bypass -Command "& '.\Configure-AdminAccess.ps1' -UserPrincipalName 'rapenmetsa@MngEnvMCAP623732.onmicrosoft.com' -SubscriptionId 'd201ebeb-c470-4a6f-82d5-c2f95bb0dc1e' -ResourceGroupName 'devops-ai-rg'"

if errorlevel 1 (
    echo.
    echo ERROR: Script execution failed. Please check the error messages above.
    echo.
    echo Make sure you have:
    echo 1. Azure PowerShell modules installed
    echo 2. Authenticated with Connect-AzAccount
    echo 3. Proper permissions on the subscription
    echo.
) else (
    echo.
    echo SUCCESS: Admin access configuration completed!
)

pause
