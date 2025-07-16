#!/bin/bash

# AI Calendar Assistant - Azure Infrastructure Deployment Script
# This script deploys the complete infrastructure using Azure Developer CLI (azd)

set -e  # Exit on any error

echo "===================================================================="
echo "AI Calendar Assistant - Infrastructure Deployment"
echo "===================================================================="
echo

# Check if azd is installed
if ! command -v azd &> /dev/null; then
    echo "❌ Azure Developer CLI (azd) is not installed or not in PATH"
    echo "Please install it from: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd"
    echo
    exit 1
fi

echo "✅ Azure Developer CLI detected"
echo

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo "🔐 Please log in to Azure..."
    az login
fi

echo "✅ Azure CLI authentication verified"
echo

# Initialize azd if needed
if [ ! -d ".azure" ]; then
    echo "🚀 Initializing Azure Developer CLI environment..."
    azd init --template . --no-prompt
    echo "✅ azd initialized successfully"
    echo
fi

# Check for required environment variables
echo "🔍 Checking required environment variables..."

missing_vars=""

if [ -z "$ENTRA_GRAPH_APPLICATION_CLIENT_ID" ]; then
    missing_vars="$missing_vars ENTRA_GRAPH_APPLICATION_CLIENT_ID"
fi
if [ -z "$ENTRA_GRAPH_APPLICATION_CLIENT_SECRET" ]; then
    missing_vars="$missing_vars ENTRA_GRAPH_APPLICATION_CLIENT_SECRET"
fi
if [ -z "$ENTRA_GRAPH_APPLICATION_TENANT_ID" ]; then
    missing_vars="$missing_vars ENTRA_GRAPH_APPLICATION_TENANT_ID"
fi

if [ -n "$missing_vars" ]; then
    echo "❌ Missing required environment variables:$missing_vars"
    echo
    echo "Please ensure your .env file contains:"
    echo "  ENTRA_GRAPH_APPLICATION_CLIENT_ID=your-client-id"
    echo "  ENTRA_GRAPH_APPLICATION_CLIENT_SECRET=your-client-secret"
    echo "  ENTRA_GRAPH_APPLICATION_TENANT_ID=your-tenant-id"
    echo
    echo "You can set these by running:"
    echo "  azd env set ENTRA_GRAPH_APPLICATION_CLIENT_ID \"your-value\""
    echo "  azd env set ENTRA_GRAPH_APPLICATION_CLIENT_SECRET \"your-value\""
    echo "  azd env set ENTRA_GRAPH_APPLICATION_TENANT_ID \"your-value\""
    echo
    exit 1
fi

echo "✅ Environment variables verified"
echo

# Set default values if not provided
if [ -z "$OPENAI_MODEL_DEPLOYMENT_NAME" ]; then
    echo "🔧 Setting default OPENAI_MODEL_DEPLOYMENT_NAME to 'gpt-4o'"
    azd env set OPENAI_MODEL_DEPLOYMENT_NAME "gpt-4o"
fi

if [ -z "$OPENAI_MODEL_NAME" ]; then
    echo "🔧 Setting default OPENAI_MODEL_NAME to 'gpt-4o'"
    azd env set OPENAI_MODEL_NAME "gpt-4o"
fi

if [ -z "$OPENAI_MODEL_VERSION" ]; then
    echo "🔧 Setting default OPENAI_MODEL_VERSION to '2024-08-06'"
    azd env set OPENAI_MODEL_VERSION "2024-08-06"
fi

if [ -z "$COSMOS_DATABASE" ]; then
    echo "🔧 Setting default COSMOS_DATABASE to 'CalendarAssistant'"
    azd env set COSMOS_DATABASE "CalendarAssistant"
fi

if [ -z "$COSMOS_CONTAINER" ]; then
    echo "🔧 Setting default COSMOS_CONTAINER to 'ChatHistory'"
    azd env set COSMOS_CONTAINER "ChatHistory"
fi

echo

# Preview deployment
echo "📋 Previewing infrastructure deployment..."
azd provision --preview

echo
echo "🔍 Deployment preview completed. Review the changes above."
echo
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r confirm
echo

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "🛑 Deployment cancelled by user"
    exit 0
fi

echo
echo "🚀 Starting infrastructure deployment..."
echo "This may take 10-15 minutes..."
echo

# Deploy infrastructure and application
azd up --no-prompt

echo
echo "🎉 Deployment completed successfully!"
echo

echo "📊 Resource Information:"
azd show --output table

echo
echo "🌐 Application URLs:"
azd env get-values | grep "AZURE_CONTAINER_APP_ENDPOINT"

echo
echo "📋 Next Steps:"
echo "  1. Test the application health endpoint"
echo "  2. Configure Microsoft Graph API permissions if needed"
echo "  3. Monitor the application in Azure Application Insights"
echo "  4. View logs with: azd logs"
echo
