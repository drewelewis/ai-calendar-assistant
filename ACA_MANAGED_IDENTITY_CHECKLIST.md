# Azure Container App Managed Identity Configuration Checklist

This checklist helps you verify that your Azure Container App (ACA) managed identity is properly configured for Azure Maps access.

## 🔍 Step-by-Step Verification

### 1. Enable Managed Identity on Container App

**Via Azure Portal:**
1. Go to Azure Portal → Container Apps
2. Select your Container App
3. Navigate to "Identity" in the left menu
4. Under "System assigned" tab:
   - Toggle "Status" to **ON**
   - Click "Save"
   - Note the "Object (principal) ID" that appears

**Via Azure CLI:**
```bash
az containerapp identity assign \
  --name <your-container-app-name> \
  --resource-group <your-resource-group> \
  --system-assigned
```

### 2. Assign Azure Maps Data Reader Role

**Via Azure Portal:**
1. Go to your Azure Maps account
2. Navigate to "Access control (IAM)"
3. Click "+ Add" → "Add role assignment"
4. Select role: **Azure Maps Data Reader**
5. Assign access to: **Managed Identity**
6. Select: **Container App** → your container app
7. Click "Save"

**Via Azure CLI:**
```bash
# Get your Container App's principal ID
PRINCIPAL_ID=$(az containerapp show \
  --name <your-container-app-name> \
  --resource-group <your-resource-group> \
  --query "identity.principalId" -o tsv)

# Get your Azure Maps account resource ID
MAPS_ID=$(az maps account show \
  --name <your-maps-account-name> \
  --resource-group <your-maps-resource-group> \
  --query "id" -o tsv)

# Assign the role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Azure Maps Data Reader" \
  --scope $MAPS_ID
```

### 3. Verify Role Assignment

**Via Azure Portal:**
1. Go to your Azure Maps account
2. Navigate to "Access control (IAM)"
3. Click "Role assignments" tab
4. Look for your Container App's managed identity with "Azure Maps Data Reader" role

**Via Azure CLI:**
```bash
# List role assignments for your Container App's managed identity
az role assignment list \
  --assignee <principal-id-from-step-1> \
  --query "[?roleDefinitionName=='Azure Maps Data Reader']" \
  -o table
```

### 4. Update Your Container App Configuration

Make sure your Container App uses managed identity instead of subscription key:

**Environment Variables to REMOVE:**
- `AZURE_MAPS_SUBSCRIPTION_KEY` (if using managed identity)

**Environment Variables to ADD (if needed):**
- `AZURE_CLIENT_ID` (only for user-assigned managed identity)

### 5. Restart Container App

**Via Azure Portal:**
1. Go to your Container App
2. Click "Restart" button
3. Wait for restart to complete

**Via Azure CLI:**
```bash
az containerapp restart \
  --name <your-container-app-name> \
  --resource-group <your-resource-group>
```

### 6. Test the Configuration

Deploy the diagnostic script to your Container App and run it:

```python
# In your Container App, run:
python check_aca_python.py
```

## 🔧 Common Issues and Solutions

### Issue: "Authentication failed" or "401 Unauthorized"
**Solutions:**
- Verify managed identity is enabled (Step 1)
- Check role assignment exists (Step 3)
- Wait 5-10 minutes for role propagation
- Restart the Container App (Step 5)

### Issue: "403 Forbidden"
**Solutions:**
- Verify the role is "Azure Maps Data Reader" (not just "Reader")
- Check the role scope includes your Azure Maps account
- Ensure the Container App and Azure Maps are in the same subscription

### Issue: "Managed identity not available"
**Solutions:**
- Confirm system-assigned identity is enabled
- Check Container App has been restarted after enabling identity
- Verify the Container App is running (not stopped)

### Issue: Role assignment appears correct but still fails
**Solutions:**
- Wait longer (role propagation can take up to 15 minutes)
- Try removing and re-adding the role assignment
- Check if there are any deny assignments that might block access

## 📝 Quick Verification Commands

Run these in your Container App environment to check status:

```bash
# Check if managed identity endpoint is available
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://atlas.microsoft.com/"

# Check environment variables
env | grep -i azure
env | grep -i identity
env | grep -i msi
```

## 🎯 Success Indicators

You know your configuration is working when:

✅ Container App has system-assigned managed identity enabled  
✅ Principal ID is visible in Azure Portal  
✅ "Azure Maps Data Reader" role is assigned to the managed identity  
✅ Role assignment scope includes your Azure Maps account  
✅ Container App has been restarted after configuration changes  
✅ Azure Maps API calls return 200 status (not 401/403)  
✅ Diagnostic script shows "✅ Azure Maps access successful with managed identity"  

## 📞 Need Help?

If you're still having issues:

1. Run the diagnostic script: `python check_aca_python.py`
2. Check the Container App logs for authentication errors
3. Verify all steps in this checklist are completed
4. Wait at least 10 minutes after making role assignment changes
5. Try removing subscription key environment variables if present
