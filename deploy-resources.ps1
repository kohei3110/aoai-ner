$AZURE_RESOURCE_GROUP = az group list --query "[?contains(name, 'rg-ner-')].{name:name}" -o tsv
$LOCATION = az group show --name $AZURE_RESOURCE_GROUP --query location -o tsv
$ACR_NAME = az acr list --query "[?contains(name, 'crner')].{name:name}" -o tsv
$ACR_REPOSITORY_NAME_ANNOTATION = "annotation"
$ACR_REPOSITORY_NAME_SEARCH = "search"
$ACR_REPOSITORY_NAME_CREATEINDEX = "createindex"
$ACE_NAME = az containerapp env list --query "[?contains(name, 'cae-ner')].name" -o tsv
$AOAI_NAME = az cognitiveservices account list --query "[?contains(name, 'oai-ner')].name" -o tsv
$AZURE_OPENAI_ENDPOINT = az cognitiveservices account show --name $AOAI_NAME --resource-group $AZURE_RESOURCE_GROUP --query "properties.endpoints" | ConvertFrom-Json | Select-Object -ExpandProperty "OpenAI Language Model Instance API"
$AZURE_OPENAI_ENDPOINT = $AZURE_OPENAI_ENDPOINT.Trim('"')
$AZURE_OPENAI_ENDPOINT = $AZURE_OPENAI_ENDPOINT.TrimEnd('/')
$AZURE_OPENAI_API_KEY = az cognitiveservices account keys list --name $AOAI_NAME --resource-group $AZURE_RESOURCE_GROUP --query "key1" -o tsv
$STORAGE_ACCOUNT_NAME = $(az storage account list --query "[?contains(name, 'stner$LOCATION')].name" -o tsv)
$STORAGE_ACCOUNT_CONNECTION_STRING = $(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $AZURE_RESOURCE_GROUP)
$AI_SEARCH_SERVICE_NAME = az search service list --resource-group $AZURE_RESOURCE_GROUP --query "[?contains(name, 'srch-ner')].{name:name}" -o tsv
$AI_SEARCH_API_KEY = az search admin-key show --service-name $AI_SEARCH_SERVICE_NAME --resource-group $AZURE_RESOURCE_GROUP --query primaryKey -o tsv

& az cognitiveservices account deployment create --name $AOAI_NAME --resource-group  $AZURE_RESOURCE_GROUP --deployment-name gpt-4o --model-name gpt-4o --model-version "2024-05-13" --model-format OpenAI --sku-capacity "30" --sku-name "Standard"
& az cognitiveservices account deployment create --name $AOAI_NAME --resource-group  $AZURE_RESOURCE_GROUP --deployment-name text-embedding-ada-002 --model-name text-embedding-ada-002 --model-version "2" --model-format OpenAI --sku-capacity "30" --sku-name "Standard"

Write-Host "========================================"
Write-Host "Login ACR"
Write-Host "========================================"
$ACR_USER = az acr credential show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP --query username -o tsv
$ACR_PASS = az acr credential show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP --query "passwords[0].value" -o tsv
az acr login -n $ACR_NAME --username $ACR_USER --password $ACR_PASS

Write-Host "========================================"
Write-Host "Build and Push (Create Annotation Job)"
Write-Host "========================================"
Set-Location -Path ./app/annotation
docker build -t "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_ANNOTATION:latest" --build-arg AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT --build-arg AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY --build-arg STORAGE_ACCOUNT_CONNECTION_STRING=$STORAGE_ACCOUNT_CONNECTION_STRING --build-arg STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME --build-arg AI_SEARCH_SERVICE_NAME=$AI_SEARCH_SERVICE_NAME --build-arg AI_SEARCH_API_KEY=$AI_SEARCH_API_KEY --platform linux/x86_64 .
docker push "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_ANNOTATION:latest"

Write-Host "========================================"
Write-Host "Build and Push (AI Search)"
Write-Host "========================================"
Set-Location ../search
docker build -t "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_SEARCH:latest" --build-arg AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT --build-arg AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY --build-arg AI_SEARCH_SERVICE_NAME=$AI_SEARCH_SERVICE_NAME --build-arg AI_SEARCH_API_KEY=$AI_SEARCH_API_KEY --platform linux/x86_64 .
docker push "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_SEARCH:latest"

Write-Host "========================================"
Write-Host "Build and Push (Create Index Job)"
Write-Host "========================================"
Set-Location ../createindex
docker build -t "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_CREATEINDEX:latest" --build-arg AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT --build-arg AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY --build-arg STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME --build-arg AI_SEARCH_SERVICE_NAME=$AI_SEARCH_SERVICE_NAME --build-arg AI_SEARCH_API_KEY=$AI_SEARCH_API_KEY --platform linux/x86_64 .
docker push "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_CREATEINDEX:latest"

Write-Host "========================================"
Write-Host "Creating Container Apps Job (Create Annotation Job)"
Write-Host "========================================"
Set-Location -Path ../search
$ACR_USER = az acr credential show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP --query username -o tsv
$ACR_PASS = az acr credential show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP --query "passwords[0].value" -o tsv
az acr login -n $ACR_NAME --username $ACR_USER --password $ACR_PASS
az containerapp job create --name cajannot-ner-demo-eastus-001 --resource-group $AZURE_RESOURCE_GROUP --environment $ACE_NAME --trigger-type Schedule --image "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_ANNOTATION:latest"  --cron-expression "30 8 * * *" --registry-server "$ACR_NAME.azurecr.io" --registry-username $ACR_USER --registry-password $ACR_PASS

Write-Host "========================================"
Write-Host "Creating Container Apps (AI Search)"
Write-Host "========================================"
Set-Location ../search
az containerapp create --name ca-ner-demo-eastus-001 --resource-group $AZURE_RESOURCE_GROUP --environment $ACE_NAME --image "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_SEARCH:latest" --registry-server "$ACR_NAME.azurecr.io" --registry-username $ACR_USER --registry-password $ACR_PASS --target-port 8000 --ingress external --query configuration.ingress.fqdn

Write-Host "========================================"
Write-Host "Creating Container Apps Job (Create Index Job)"
Write-Host "========================================"
Set-Location ../createindex
$ACR_USER = az acr credential show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP --query username -o tsv
$ACR_PASS = az acr credential show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP --query "passwords[0].value" -o tsv
az acr login -n $ACR_NAME --username $ACR_USER --password $ACR_PASS
az containerapp job create --name cajindex-ner-demo-eastus-001 --resource-group $AZURE_RESOURCE_GROUP --environment $ACE_NAME --trigger-type Schedule --image "$ACR_NAME.azurecr.io/$ACR_REPOSITORY_NAME_CREATEINDEX:latest"  --cron-expression "0 9 * * *" --registry-server "$ACR_NAME.azurecr.io" --registry-username $ACR_USER --registry-password $ACR_PASS