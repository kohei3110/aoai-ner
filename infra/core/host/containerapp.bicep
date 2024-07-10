param containerAppEnvironmentName string
param containerAppName string
param location string = resourceGroup().location
param tags object = {}

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: containerAppEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'azure-monitor'
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: containerAppName
  location: location
  tags: tags
  properties: {
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: {
        allowInsecure: false
        clientCertificateMode: 'ignore'
        external: true
        targetPort: 8000
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'app'
          image: 'named-entity-recognition-copy/aisearch-dev:azd-deploy-1720077864'
          resources: {
            cpu: json('1.0')
            memory: '2.0Gi'
          }
        }
      ]
    }
    environmentId: containerAppEnvironment.id
  }
}
