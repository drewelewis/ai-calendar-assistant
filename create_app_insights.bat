@echo off
echo Creating Application Insights resource...

REM Create Application Insights without workspace dependency
az monitor app-insights component create ^
    --app ai-calendar-assistant-insights ^
    --location eastus ^
    --resource-group devops-ai-rg ^
    --application-type web ^
    --subscription d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e

if %errorlevel% neq 0 (
    echo Failed to create Application Insights
    exit /b 1
)

echo Getting connection string...
az monitor app-insights component show ^
    --app ai-calendar-assistant-insights ^
    --resource-group devops-ai-rg ^
    --subscription d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e ^
    --query connectionString ^
    --output tsv

echo Done!
