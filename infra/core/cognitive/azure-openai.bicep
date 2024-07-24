param location string
param openAiName string
param openAiSku string
param openAiCustomSubDomainName string
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
