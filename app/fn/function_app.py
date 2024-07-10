# FIX issue: https://github.com/microsoft/Oryx/issues/1774#issuecomment-1671958417

import azure.functions as func
from tenacity import retry, wait_random_exponential, stop_after_attempt

from main.domain.service.entity_labels_service import EntityLabelsService
from main.infrastructure.datasource.config.azure_openai_repository import AzureOpenAIRepository

def setup_logging():
    import logging
    logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')

def get_text_from_request(req: func.HttpRequest):
    return req.get_json().get('text')

def create_client():
    return AzureOpenAIRepository().create_openai_client()

labels = EntityLabelsService.get_labels()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
@app.route(route="annotations/enrich", methods=["POST"])
def create_annotations_enrich(req: func.HttpRequest) -> func.HttpResponse:
    from main.application.usecase.create_annotations_enrich_usecase import CreateAnnotationsEnrichUseCase
    from main.application.factory.message_factory import MessageFactory
    setup_logging()
    client = create_client()
    text = get_text_from_request(req)
    return CreateAnnotationsEnrichUseCase.create(CreateAnnotationsEnrichUseCase(client=client), text, labels, MessageFactory.system_message, MessageFactory.assisstant_message, MessageFactory.user_message_enrich_enable)

@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
@app.route(route="annotations", methods=["POST"])
def create_annotations(req: func.HttpRequest) -> func.HttpResponse:
    from main.application.factory.create_annotations_factory import CreateAnnotationsFactory
    from main.application.factory.message_factory import MessageFactory
    setup_logging()
    client = create_client()
    create_annotations_usecase = CreateAnnotationsFactory.inject_usecase(client)
    response = create_annotations_usecase.create(get_text_from_request(req), labels, MessageFactory.system_message, MessageFactory.assisstant_message, MessageFactory.user_message_enrich_disable)
    # Blob Storage に保存
    create_annotations_usecase.save(response)
    return func.HttpResponse(response, status_code=200)


# This function will be triggered every day at 19:30 UTC (26:30 AM JST)
@app.timer_trigger(schedule="0 30 19 * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def daily_sync_records(myTimer: func.TimerRequest) -> None:
    print('アノテーション付与処理を実行します。（モック）')
