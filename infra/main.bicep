// AI Calendar Assistant - Main Infrastructure Template
// This template deploys all Azure resources needed for the AI Calendar Assistant
// including Container Apps, Azure OpenAI, CosmosDB, Key Vault, and Application Insights

@description('Environment name for resource naming')
param environmentName string

@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Resource group name')
param resourceGroupName string

@description('Azure OpenAI model deployment name')
param openAIModelDeploymentName string = 'gpt-4o'

@description('Azure OpenAI model name')
param openAIModelName string = 'gpt-4o'

@description('Azure OpenAI model version')
param openAIModelVersion string = '2024-08-06'

@description('CosmosDB database name')
param cosmosDbDatabaseName string = 'CalendarAssistant'

@description('CosmosDB container name')
param cosmosDbContainerName string = 'ChatHistory'

@description('Microsoft Graph Application Client ID (from Entra)')
@secure()
param entraGraphClientId string

@description('Microsoft Graph Application Client Secret (from Entra)')
@secure()
param entraGraphClientSecret string

@description('Microsoft Graph Application Tenant ID (from Entra)')
param entraGraphTenantId string

// Generate unique resource token for naming
var resourceToken = toLower(uniqueString(subscription().id, resourceGroup().id, environmentName))
var resourcePrefix = 'cal-assist'

// Tags for all resources
var commonTags = {
  'azd-env-name': environmentName
  'azd-service-name': 'ai-calendar-assistant'
  'azd-service-type': 'containerapp'
  application: 'ai-calendar-assistant'
  environment: environmentName
}

//=============================================================================
// SHARED RESOURCES
//=============================================================================

// Log Analytics Workspace for monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${resourcePrefix}-logs-${resourceToken}'
  location: location
  tags: commonTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
    features: {
      searchVersion: 1
      legacy: 0
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Application Insights for telemetry
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${resourcePrefix}-ai-${resourceToken}'
  location: location
  tags: commonTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// User-assigned managed identity for secure access
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${resourcePrefix}-identity-${resourceToken}'
  location: location
  tags: commonTags
}

// Key Vault for storing sensitive configuration
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${resourcePrefix}-kv-${resourceToken}'
  location: location
  tags: commonTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: managedIdentity.properties.principalId
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Store Microsoft Graph secrets in Key Vault
resource entraClientIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'ENTRA-GRAPH-APPLICATION-CLIENT-ID'
  properties: {
    value: entraGraphClientId
    contentType: 'application/text'
  }
}

resource entraClientSecretSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'ENTRA-GRAPH-APPLICATION-CLIENT-SECRET'
  properties: {
    value: entraGraphClientSecret
    contentType: 'application/text'
  }
}

resource entraTenantIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'ENTRA-GRAPH-APPLICATION-TENANT-ID'
  properties: {
    value: entraGraphTenantId
    contentType: 'application/text'
  }
}

//=============================================================================
// AZURE OPENAI SERVICE
//=============================================================================

resource openAI 'Microsoft.CognitiveServices/accounts@2024-06-01-preview' = {
  name: '${resourcePrefix}-openai-${resourceToken}'
  location: location
  tags: commonTags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${resourcePrefix}-openai-${resourceToken}'
    networkAcls: {
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true // Use managed identity instead of keys
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Deploy the specified OpenAI model
resource openAIDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
  parent: openAI
  name: openAIModelDeploymentName
  properties: {
    model: {
      format: 'OpenAI'
      name: openAIModelName
      version: openAIModelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
  sku: {
    name: 'Standard'
    capacity: 30
  }
}

// Role assignment for managed identity to access OpenAI
resource openAIRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: openAI
  name: guid(openAI.id, managedIdentity.id, 'Cognitive Services OpenAI User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

//=============================================================================
// COSMOS DB
//=============================================================================

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: '${resourcePrefix}-cosmos-${resourceToken}'
  location: location
  tags: commonTags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    isVirtualNetworkFilterEnabled: false
    virtualNetworkRules: []
    ipRules: []
    disableKeyBasedMetadataWriteAccess: true // Use RBAC instead of keys
    enableFreeTier: false
    enableAnalyticalStorage: false
    analyticalStorageConfiguration: {
      schemaType: 'WellDefined'
    }
    publicNetworkAccess: 'Enabled'
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosDbAccount
  name: cosmosDbDatabaseName
  properties: {
    resource: {
      id: cosmosDbDatabaseName
    }
  }
}

resource cosmosDbContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDbDatabase
  name: cosmosDbContainerName
  properties: {
    resource: {
      id: cosmosDbContainerName
      partitionKey: {
        paths: ['/session_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'Consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: -1
    }
  }
}

// Role assignment for managed identity to access CosmosDB
resource cosmosDbRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-05-15' = {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, 'sql-role-definition')
  properties: {
    roleName: 'AI Calendar Assistant CosmosDB Data Contributor'
    type: 'CustomRole'
    assignableScopes: [
      cosmosDbAccount.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
        ]
      }
    ]
  }
}

resource cosmosDbRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, managedIdentity.id, 'sql-role-assignment')
  properties: {
    roleDefinitionId: cosmosDbRoleDefinition.id
    principalId: managedIdentity.properties.principalId
    scope: cosmosDbAccount.id
  }
}

//=============================================================================
// CONTAINER REGISTRY
//=============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${resourcePrefix}cr${resourceToken}'
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    policies: {
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 7
        status: 'disabled'
      }
    }
    encryption: {
      status: 'disabled'
    }
    dataEndpointEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    zoneRedundancy: 'Disabled'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Role assignment for managed identity to pull from container registry
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(containerRegistry.id, managedIdentity.id, 'AcrPull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

//=============================================================================
// CONTAINER APPS ENVIRONMENT
//=============================================================================

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${resourcePrefix}-env-${resourceToken}'
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    zoneRedundant: false
    kedaConfiguration: {}
    daprConfiguration: {}
    customDomainConfiguration: {}
  }
}

//=============================================================================
// CONTAINER APP
//=============================================================================

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${resourcePrefix}-app-${resourceToken}'
  location: location
  tags: union(commonTags, {
    'azd-service-name': 'ai-calendar-assistant'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8989
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: false
        }
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: managedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'entra-client-id'
          keyVaultUrl: entraClientIdSecret.properties.secretUri
          identity: managedIdentity.id
        }
        {
          name: 'entra-client-secret'
          keyVaultUrl: entraClientSecretSecret.properties.secretUri
          identity: managedIdentity.id
        }
        {
          name: 'entra-tenant-id'
          keyVaultUrl: entraTenantIdSecret.properties.secretUri
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          name: 'ai-calendar-assistant'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'OPENAI_ENDPOINT'
              value: openAI.properties.endpoint
            }
            {
              name: 'OPENAI_API_VERSION'
              value: '2024-08-06'
            }
            {
              name: 'OPENAI_MODEL_DEPLOYMENT_NAME'
              value: openAIModelDeploymentName
            }
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmosDbAccount.properties.documentEndpoint
            }
            {
              name: 'COSMOS_DATABASE'
              value: cosmosDbDatabaseName
            }
            {
              name: 'COSMOS_CONTAINER'
              value: cosmosDbContainerName
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsights.properties.ConnectionString
            }
            {
              name: 'ENTRA_GRAPH_APPLICATION_CLIENT_ID'
              secretRef: 'entra-client-id'
            }
            {
              name: 'ENTRA_GRAPH_APPLICATION_CLIENT_SECRET'
              secretRef: 'entra-client-secret'
            }
            {
              name: 'ENTRA_GRAPH_APPLICATION_TENANT_ID'
              secretRef: 'entra-tenant-id'
            }
            {
              name: 'TELEMETRY_SERVICE_NAME'
              value: 'ai-calendar-assistant'
            }
            {
              name: 'TELEMETRY_SERVICE_VERSION'
              value: '1.0.0'
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: managedIdentity.properties.clientId
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8989
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8989
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

//=============================================================================
// OUTPUTS
//=============================================================================

@description('The endpoint URL of the deployed Container App')
output AZURE_CONTAINER_APP_ENDPOINT string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('The name of the Container App')
output AZURE_CONTAINER_APP_NAME string = containerApp.name

@description('The name of the Container Registry')
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name

@description('The login server of the Container Registry')
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer

@description('The OpenAI service endpoint')
output OPENAI_ENDPOINT string = openAI.properties.endpoint

@description('The OpenAI model deployment name')
output OPENAI_MODEL_DEPLOYMENT_NAME string = openAIModelDeploymentName

@description('The CosmosDB endpoint')
output COSMOS_ENDPOINT string = cosmosDbAccount.properties.documentEndpoint

@description('The CosmosDB database name')
output COSMOS_DATABASE string = cosmosDbDatabaseName

@description('The CosmosDB container name')
output COSMOS_CONTAINER string = cosmosDbContainerName

@description('The Application Insights connection string')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.properties.ConnectionString

@description('The Application Insights name')
output AZURE_APPLICATION_INSIGHTS_NAME string = applicationInsights.name

@description('The Key Vault name')
output AZURE_KEY_VAULT_NAME string = keyVault.name

@description('The managed identity client ID')
output AZURE_CLIENT_ID string = managedIdentity.properties.clientId

@description('The resource group name')
output AZURE_RESOURCE_GROUP string = resourceGroupName

@description('The resource group ID')
output RESOURCE_GROUP_ID string = resourceGroup().id

@description('The environment name')
output AZURE_ENV_NAME string = environmentName

@description('The primary location')
output AZURE_LOCATION string = location
