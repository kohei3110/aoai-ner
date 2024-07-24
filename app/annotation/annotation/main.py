import asyncio
import logging
import sys
import warnings
from fastapi import HTTPException

from application.factory.message_factory import MessageFactory
from domain.service.entity_labels_service import EntityLabelsService
from infrastructure.datasource.config.azure_openai_repository import AzureOpenAIRepository
from model.inquiry_request import InquiryRequest

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')

def create_client():
    return AzureOpenAIRepository().create_openai_client()

labels = EntityLabelsService.get_labels()

async def schedule():
    from application.factory.create_annotations_factory import CreateAnnotationsFactory  # Lazy import
    client = create_client()
    create_annotations_usecase = CreateAnnotationsFactory.inject_usecase(client)

    try:

        # TODO: Outlook のメール本文を取得
        req = InquiryRequest(text="今日はxxx株式会社のyyy様と、zzz製品の打ち合わせを行いました。")

        response = create_annotations_usecase.create(get_text_from_request(req), labels, MessageFactory.system_message, MessageFactory.assisstant_message, MessageFactory.user_message_enrich_disable)
        # Blob Storage に保存
        create_annotations_usecase.save(response)
        sys.exit(0)
    except Exception as e:
        logging.error(e)
        sys.exit(1)

def get_text_from_request(req: InquiryRequest) -> str:
    try:
        return req.text
    except AttributeError:
        raise HTTPException(status_code=400, detail="Invalid request format.")
    
async def main():
    await schedule()

if __name__ == "__main__":
    asyncio.run(schedule())