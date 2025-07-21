@echo off
echo 🔄 Restarting Azure Container App
echo ===============================

echo.
echo 📋 Current container app status:
az containerapp show --name ai-calendar-assistant --resource-group devops-ai-rg --query "{name:name,state:properties.runningStatus}" -o table

echo.
echo 🔄 Restarting container app...
az containerapp restart --name ai-calendar-assistant --resource-group devops-ai-rg

echo.
echo ⏳ Waiting for restart to complete...
timeout /t 10 /nobreak > nul

echo.
echo 📋 Updated container app status:
az containerapp show --name ai-calendar-assistant --resource-group devops-ai-rg --query "{name:name,state:properties.runningStatus,fqdn:properties.configuration.ingress.fqdn}" -o table

echo.
echo ✅ Container app restart complete!
echo 💡 You can now test your Azure Maps API calls.
