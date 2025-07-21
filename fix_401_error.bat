REM Azure Maps 401 Error Fix Commands
REM Run these commands in order to diagnose and fix your authentication issue

echo "=== STEP 1: Check Container App Managed Identity ==="
az containerapp identity show --name aiwrapper --resource-group devops-ai-rg

echo.
echo "=== STEP 2: Check Current Role Assignments ==="
az role assignment list --assignee 5238e629-da2f-4bb0-aea5-14d45526c864 --all --output table

echo.
echo "=== STEP 3: Find Azure Maps Account ==="
az maps account list --subscription d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e --output table

echo.
echo "=== STEP 4: Check Azure Maps Account Authentication Configuration ==="
az maps account show --name azure-maps-instance --resource-group devops-ai-rg --subscription d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e --query "properties.disableLocalAuth"

echo.
echo "=== STEP 5: CRITICAL - Enable Azure AD Authentication on Azure Maps Account ==="
echo "This is the most likely fix for your 401 error!"
az maps account update --name azure-maps-instance --resource-group devops-ai-rg --disable-local-auth true

echo.
echo "=== STEP 6: Verify Role Assignment (if needed) ==="
az role assignment create --assignee 5238e629-da2f-4bb0-aea5-14d45526c864 --role "Azure Maps Data Reader" --scope "/subscriptions/d201ebeb-c470-4a6f-82d5-c2f95bb0dc1e/resourceGroups/devops-ai-rg/providers/Microsoft.Maps/accounts/azure-maps-instance"

echo.
echo "=== STEP 7: Restart Container App ==="
az containerapp restart --name aiwrapper --resource-group devops-ai-rg

echo.
echo "=== TROUBLESHOOTING COMPLETED ==="
echo "The most common fix is Step 5 - enabling Azure AD auth on the Maps account!"
echo "After running these commands, test your application again."
