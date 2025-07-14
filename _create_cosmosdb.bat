@echo off
REM CosmosDB Creation Script for AI Calendar Assistant
echo Creating Azure CosmosDB resources...

REM Set variables
set RESOURCE_GROUP=devops-ai-rg
set LOCATION=eastus
set COSMOS_ACCOUNT_NAME=ai-calendar-assistant-cosmosdb
set DATABASE_NAME=CalendarAssistant
set CONTAINER_NAME=ChatHistory

REM Create resource group if it doesn't exist
@REM echo Creating resource group...
@REM call az group create --name %RESOURCE_GROUP% --location %LOCATION%

REM Create CosmosDB account
echo Creating CosmosDB account...
call az cosmosdb create ^
  --name %COSMOS_ACCOUNT_NAME% ^
  --resource-group %RESOURCE_GROUP% ^
  --kind GlobalDocumentDB ^
  --default-consistency-level Session ^
  --enable-free-tier false

REM Create database
echo Creating database...
call az cosmosdb sql database create ^
  --account-name %COSMOS_ACCOUNT_NAME% ^
  --resource-group %RESOURCE_GROUP% ^
  --name %DATABASE_NAME%

REM Create container with /sessionId as partition key
echo Creating container...
call az cosmosdb sql container create ^
  --account-name %COSMOS_ACCOUNT_NAME% ^
  --resource-group %RESOURCE_GROUP% ^
  --database-name %DATABASE_NAME% ^
  --name %CONTAINER_NAME% ^
  --partition-key-path "/sessionId" ^
  --throughput 400

REM Get connection string
echo Getting connection keys...
call az cosmosdb keys list ^
  --name %COSMOS_ACCOUNT_NAME% ^
  --resource-group %RESOURCE_GROUP% ^
  --type keys

echo CosmosDB resources created successfully.
echo Add the following to your .env file:
echo COSMOS_ENDPOINT=https://%COSMOS_ACCOUNT_NAME%.documents.azure.com:443/
echo COSMOS_KEY=(primary key from above output)
echo COSMOS_DATABASE=%DATABASE_NAME%
echo COSMOS_CONTAINER=%CONTAINER_NAME%