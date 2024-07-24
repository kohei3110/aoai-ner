param containerAppEnvironmentName string
param location string = resourceGroup().location
param tags object = {}
param customerId string
param sharedKey string

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: containerAppEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: customerId
        dynamicJsonColumns: false
        sharedKey: sharedKey
      }
    }
  }
}
