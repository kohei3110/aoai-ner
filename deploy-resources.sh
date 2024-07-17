#!/bin/bash

AZURE_RESOURCE_GROUP=`az group list --query "[?contains(name, 'rg-ner-')].{name:name}" -o tsv`
ACR_NAME=`az acr list --query "[?contains(name, 'crner')].{name:name}" -o tsv`
ACR_REPOSITORY_NAME_SEARCH=search
ACR_REPOSITORY_NAME_CREATEINDEX=createindex
ACE_NAME=`az containerapp env list --query "[?contains(name, 'cae-ner')].name" -o tsv`
FN_APP_NAME=`az functionapp list --query "[?contains(name, 'func-ner')].name" -o tsv`
AOAI_NAME=`az cognitiveservices account list --query "[?contains(name, 'oai-ner')].name" -o tsv`

echo "========================================"
echo "Deploy Function App (Flex Consumption)"
echo "========================================"
cd ./app/fn
func azure functionapp publish ${FN_APP_NAME} --python

echo "========================================"
echo "Login ACR"
echo "========================================"
ACR_USER=`az acr credential show --name ${ACR_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --query username -o tsv`
ACR_PASS=`az acr credential show --name ${ACR_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --query "passwords[0].value" -o tsv`
az acr login -n ${ACR_NAME} --username ${ACR_USER} --password ${ACR_PASS}

echo "========================================"
echo "Build and Push (AI Search)"
echo "========================================"
cd ../search
docker build -t ${ACR_NAME}.azurecr.io/${ACR_REPOSITORY_NAME_SEARCH}:latest --platform linux/x86_64 .
docker push ${ACR_NAME}.azurecr.io/${ACR_REPOSITORY_NAME_SEARCH}:latest

echo "========================================"
echo "Build and Push (Create Index Job)"
echo "========================================"
cd ../createindex
docker build -t ${ACR_NAME}.azurecr.io/${ACR_REPOSITORY_NAME_CREATEINDEX}:latest --platform linux/x86_64 .
docker push ${ACR_NAME}.azurecr.io/${ACR_REPOSITORY_NAME_CREATEINDEX}:latest

echo "========================================"
echo "Creating Container Apps (AI Search)"
echo "========================================"
cd ../search
az containerapp create --name ca-ner-demo-eastus-001 --resource-group ${AZURE_RESOURCE_GROUP} --environment ${ACE_NAME} --image ${ACR_NAME}.azurecr.io/${ACR_REPOSITORY_NAME_SEARCH}:latest --registry-server ${ACR_NAME}.azurecr.io --registry-username ${ACR_USER} --registry-password ${ACR_PASS} --target-port 8000 --ingress external --query configuration.ingress.fqdn

echo "========================================"
echo "Creating Container Apps Job (Create Index Job)"
echo "========================================"
cd ../createindex
ACR_USER=`az acr credential show --name ${ACR_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --query username -o tsv`
ACR_PASS=`az acr credential show --name ${ACR_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --query "passwords[0].value" -o tsv`
az acr login -n ${ACR_NAME} --username ${ACR_USER} --password ${ACR_PASS}
az containerapp job create --name caj-ner-demo-eastus-001 --resource-group ${AZURE_RESOURCE_GROUP} --environment ${ACE_NAME} --trigger-type Schedule --image ${ACR_NAME}.azurecr.io/${ACR_REPOSITORY_NAME_CREATEINDEX}:latest  --cron-expression "0 9 * * *" --registry-server ${ACR_NAME}.azurecr.io --registry-username ${ACR_USER} --registry-password ${ACR_PASS}

echo "========================================"
echo "Setting Functions environment variables"
echo "========================================"
AOAI_ENDPOINT=`az cognitiveservices account show --name ${AOAI_NAME} --resource-group ${AZURE_RESOURCE_GROUP} | jq -r .properties.endpoint`
AZURE_OPENAI_API_KEY=`az cognitiveservices account keys list --name ${AOAI_NAME} --resource-group  ${AZURE_RESOURCE_GROUP} | jq -r .key1`
az functionapp config appsettings set --name ${FN_APP_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --settings AOAI_ENDPOINT=${AOAI_ENDPOINT}
az functionapp config appsettings set --name ${FN_APP_NAME} --resource-group ${AZURE_RESOURCE_GROUP} --settings AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}