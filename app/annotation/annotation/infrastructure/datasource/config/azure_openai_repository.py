import os
from openai import AzureOpenAI

from application.factory.openai_client_factory import OpenAIClientFactory

class AzureOpenAIRepository(OpenAIClientFactory):
    @staticmethod
    def create_openai_client():
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )