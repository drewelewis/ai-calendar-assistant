@echo off
echo ===============================================
echo AI Calendar Assistant - Admin Access Setup
echo ===============================================
echo.
echo User: rapenmetsa@MngEnvMCAP623732.onmicrosoft.com
echo Subscription: d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e
echo Resource Group: devops-ai-rg
echo.
echo This script will:
echo 1. Install required Azure PowerShell modules
echo 2. Authenticate with Azure (if needed)
echo 3. Configure admin access for the specified user
echo.
pause

powershell -ExecutionPolicy Bypass -File "Configure-AdminAccess-Simple.ps1" -UserPrincipalName "rapenmetsa@MngEnvMCAP623732.onmicrosoft.com" -SubscriptionId "d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e" -ResourceGroupName "devops-ai-rg"

echo.
echo Script execution completed.
pause
