targetScope = 'subscription'

@minLength(1)
@maxLength(10)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string
@minLength(1)
@description('Primary location for all resources')
@allowed(['australiaeast', 'eastasia', 'eastus', 'eastus2', 'northeurope', 'southcentralus', 'southeastasia', 'swedencentral', 'uksouth', 'westus2'])
param location string 
param resourceGroupName string = ''
param logAnalyticsName string = ''
param applicationInsightsName string = ''

var abbrs = loadJsonContent('./abbreviations.json')

// Generate a unique token to be used in naming resources.
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// tags that should be applied to all resources.
var tags = {
  'azd-env-name': environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  location: location
  tags: tags
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}ner-${environmentName}-${location}-001'
}

// Monitor application with Azure Monitor
module monitoring 'shared/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: !empty(logAnalyticsName) ? logAnalyticsName : '${abbrs.operationalInsightsWorkspaces}ner-${environmentName}-${location}-001'
    applicationInsightsName: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}ner-${environmentName}-${location}-001'
  }
}

module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    documentStorageName: '${abbrs.storageStorageAccounts}ner${location}${resourceToken}'
  }
}

module azureOpenAi 'core/cognitive/azure-openai.bicep' = {
  name: 'azureOpenAi'
  scope: rg
  params: {
    location: location
    tags: tags
    openAiName: 'oai-ner-${environmentName}-${location}-001'
    openAiSku: 'S0'
    openAiCustomSubDomainName:'${abbrs.cognitiveServicesAccounts}${resourceToken}'
  }
}

module aiSearch 'core/cognitive/aisearch.bicep' = {
  name: 'aiSearch'
  scope: rg
  params: {
    name: '${abbrs.searchSearchServices}ner-${environmentName}-${location}-001'
    location: location
    sku: 'standard'
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

module containerAppEnv 'core/host/containerapp.bicep' = {
  name: 'containerappenv'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppEnvironmentName: '${abbrs.appManagedEnvironments}ner-${environmentName}-${location}-001'
    customerId: monitoring.outputs.logAnalyticsCustomerId
    sharedKey: monitoring.outputs.logAnalyticsPrimaryKey
  }
}

module containerRegistry 'shared/container/registry.bicep' = {
  name: '${abbrs.containerRegistryRegistries}${environmentName}${location}${deployment().name}${resourceToken}001'
  scope: resourceGroup(rg.name)
  params: {
    acrName: '${abbrs.containerRegistryRegistries}ner${environmentName}${location}001'
    location: location
    acrSku: 'Basic'
  }
}
