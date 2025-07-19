# Azure Managed Identity 401 Error - Troubleshooting Guide

## 🚨 **Problem Identified**

Your managed identity `5238e629-da2f-4bb0-aea5-14d45526c864` is successfully getting an access token, but Azure Maps is rejecting it with a **401 Unauthorized** error.

## 🔍 **Root Cause Analysis**

The error message shows:
```
"Bearer realm=\"https://atlas.microsoft.com/\", SharedKey realm=\"https://atlas.microsoft.com/\""
```

This indicates that Azure Maps expects either:
1. A valid Bearer token with proper permissions, OR
2. A SharedKey (subscription key)

Since your token is being acquired but rejected, the issue is **role assignment scope or configuration**.

## 🎯 **Most Likely Causes**

### **1. Role Assignment Scope Issue (Most Common)**
- Role might be assigned to the **wrong scope** (subscription or resource group instead of the Azure Maps account)
- Role needs to be assigned directly to the **Azure Maps resource**

### **2. Role Assignment Missing or Incorrect**
- The managed identity doesn't have the role assigned at all
- Wrong role assigned (should be "Azure Maps Data Reader")

### **3. Role Propagation Delay**
- Role was recently assigned but hasn't propagated yet (can take 10-15 minutes)

## 🔧 **Step-by-Step Fix**

### **Step 1: Verify Role Assignment in Azure Portal**

1. Go to **Azure Portal** → **Azure Maps**
2. Select your **Azure Maps account**
3. Click **Access control (IAM)** in the left menu
4. Click the **"Role assignments"** tab
5. Look for your Container App's managed identity: `5238e629-da2f-4bb0-aea5-14d45526c864`

### **Step 2: Check Current Role Assignment**

You should see:
- **Role**: "Azure Maps Data Reader" ✅
- **Assigned to**: Your Container App's managed identity ✅
- **Scope**: Your Azure Maps account (NOT subscription or resource group) ✅

### **Step 3: Fix Role Assignment if Wrong Scope**

If the role is assigned to subscription or resource group:

1. **Remove** the existing role assignment
2. **Add new role assignment**:
   - Role: **"Azure Maps Data Reader"**
   - Assign access to: **"Managed Identity"**
   - Managed identity: **"Container App"** → Select your Container App
   - Scope: **Azure Maps account** (this resource)

### **Step 4: Add Role Assignment if Missing**

If no role assignment exists:

1. Click **"+ Add"** → **"Add role assignment"**
2. **Select role**: "Azure Maps Data Reader"
3. Click **"Next"**
4. **Assign access to**: "Managed Identity"
5. **Click "+ Select members"**
6. **Managed identity**: "Container App"
7. **Select your Container App** from the list
8. Click **"Select"**
9. Click **"Review + assign"**
10. Click **"Assign"**

### **Step 5: Verify the Assignment**

After adding the role:
1. Go back to **Role assignments** tab
2. Verify you see:
   ```
   Azure Maps Data Reader | Container App: <your-app-name> | This resource
   ```

### **Step 6: Restart and Wait**

1. **Restart your Container App**:
   - Go to Container Apps → Your app → Click "Restart"
2. **Wait 10-15 minutes** for role propagation
3. **Test again**

## 🧪 **Quick Test Commands**

### **Azure CLI Verification**
```bash
# Check role assignments for your managed identity
az role assignment list \
  --assignee 5238e629-da2f-4bb0-aea5-14d45526c864 \
  --query "[?roleDefinitionName=='Azure Maps Data Reader']" \
  -o table

# Should show your Azure Maps account in the scope
```

### **PowerShell Verification**
```powershell
# Get role assignments for the managed identity
Get-AzRoleAssignment -ObjectId 5238e629-da2f-4bb0-aea5-14d45526c864 | 
Where-Object {$_.RoleDefinitionName -eq "Azure Maps Data Reader"}
```

## 📋 **Checklist**

- [ ] Managed identity has "Azure Maps Data Reader" role
- [ ] Role is assigned to the **Azure Maps account** (not subscription/RG)
- [ ] Role assignment shows principal ID: `5238e629-da2f-4bb0-aea5-14d45526c864`
- [ ] Container App has been restarted after role assignment
- [ ] Waited 10-15 minutes after role assignment changes
- [ ] No subscription key environment variable in Container App

## 🎯 **Expected Result**

After fixing the role assignment, your debug logs should show:
```
✅ Token acquired successfully!
✅ Token audience is correct for Azure Maps
✅ Successfully geocoded Charlotte, NC
```

## 🆘 **If Still Not Working**

1. **Double-check Azure Maps account region** matches your Container App region
2. **Verify Azure Maps account is active** and not suspended
3. **Check if there are any deny assignments** in Access Control (IAM)
4. **Try creating a new role assignment** with a different managed identity
5. **Contact Azure support** if the issue persists

The enhanced debug logging will now show you exactly what's in the token and help identify if the audience or other token properties are incorrect.
