@echo off
echo 🔍 Verifying Azure Maps Account Configuration
echo ============================================

echo.
echo 📋 Checking disableLocalAuth setting...
az maps account show --name azure-maps-instance --resource-group devops-ai-rg --query "properties.disableLocalAuth" -o table

echo.
echo 📋 Checking Azure Maps account details...
az maps account show --name azure-maps-instance --resource-group devops-ai-rg --query "{name:name,sku:sku.name,disableLocalAuth:properties.disableLocalAuth}" -o table

echo.
echo 📋 Checking Container App status...
az containerapp show --name ai-calendar-assistant --resource-group devops-ai-rg --query "{name:name,fqdn:properties.configuration.ingress.fqdn,state:properties.runningStatus}" -o table

echo.
echo ✅ Configuration check complete!
echo.
echo 💡 Next steps if disableLocalAuth is true:
echo    1. Restart your container app (if not done already)
echo    2. Test the Azure Maps API calls
echo    3. Monitor application logs for any remaining issues
