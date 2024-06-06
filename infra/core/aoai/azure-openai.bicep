param location string
param openAiName string
param openAiSku string
param openAiCustomSubDomainName string
param gpt4ModelCapacity int
param gpt4ModelVersion string
param tags object = {}

resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: openAiSku
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: openAiCustomSubDomainName
  }
  tags: tags
}

resource gpt4oModel 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: gpt4ModelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: gpt4ModelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}
