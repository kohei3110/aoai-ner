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
param functionPlanName string = ''
param functionAppName string = ''
param storageAccountName string = ''
param documentStorageAccountName string = ''
param logAnalyticsName string = ''
param applicationInsightsName string = ''
@allowed(['dotnet-isolated','python','java', 'node', 'powerShell'])
param functionAppRuntime string = 'python'
@allowed(['3.10','3.11'])
param functionAppRuntimeVersion string = '3.11'
@minValue(40)
@maxValue(1000)
param maximumInstanceCount int = 100
@allowed([2048,4096])
param instanceMemoryMB int = 2048

var abbrs = loadJsonContent('./abbreviations.json')
// Generate a unique token to be used in naming resources.
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
// Generate a unique function app name if one is not provided.
var appName = !empty(functionAppName) ? functionAppName : '${abbrs.webSitesFunctions}ner-${environmentName}-${location}-001'
// Generate a unique container name that will be used for deployments.
var deploymentStorageContainerName = 'app-package-${take(appName, 32)}-${take(resourceToken, 7)}'
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

// Backing storage for Azure Functions
module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    location: location
    tags: tags
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    documentStorageName: !empty(documentStorageAccountName) ? documentStorageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}docs'
    containers: [{name: deploymentStorageContainerName}]
  }
}

// Azure Functions Flex Consumption
module flexFunction 'core/host/function.bicep' = {
  name: 'functionapp'
  scope: rg
  params: {
    location: location
    tags: tags
    planName: !empty(functionPlanName) ? functionPlanName : '${abbrs.webServerFarms}ner-${environmentName}-${location}-001'
    appName: appName
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    storageAccountName: storage.outputs.name
    deploymentStorageContainerName: deploymentStorageContainerName
    functionAppRuntime: functionAppRuntime
    functionAppRuntimeVersion: functionAppRuntimeVersion
    maximumInstanceCount: maximumInstanceCount
    instanceMemoryMB: instanceMemoryMB    
  }
}

module azureOpenAi 'core/aoai/azure-openai.bicep' = {
  name: 'azureOpenAi'
  scope: rg
  params: {
    location: location
    tags: tags
    gpt4ModelCapacity: 1
    openAiName: 'oai-ner-${environmentName}-${location}-001'
    openAiSku: 'S0'
    openAiCustomSubDomainName:'${abbrs.cognitiveServicesAccounts}${resourceToken}'
    gpt4ModelVersion: '2024-05-13'
  }
}

module containerApp 'core/host/containerapp.bicep' = {
  name: 'containerapp'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppEnvironmentName: '${abbrs.appManagedEnvironments}ner-${environmentName}-${location}-001'
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
