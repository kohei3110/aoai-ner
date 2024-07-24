import datetime
import os
import logging
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient

class CreateAnnotationsUseCase:
    def __init__(self, client):
        self.client = client
        logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')

    def create_messages(self, text, labels, system_message, assistant_message, user_message):
        messages = [
            {"role": "system", "content": system_message(labels=labels)},
            {"role": "assistant", "content": assistant_message()},
            {"role": "user", "content": user_message(text=text)}
        ]
        return messages

    def create(self, text, labels, system_message, assistant_message, user_message):
        messages = self.create_messages(text, labels, system_message, assistant_message, user_message)
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("MODEL_ID"),
                messages=messages, 
                temperature=0.0,
            )
            return response.choices[0].message.content
        except AzureError as e:
            logging.error(f"An error occurred: {e}")
        
    def save(self, response):
        # Blob Storage に保存
        now_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        blob_client = BlobClient.from_connection_string(os.environ.get("STORAGE_ACCOUNT_CONNECTION_STRING"), "cog-search-demo", now_str + ".json")
        # 日時をファイル名に含める
        blob_client.upload_blob(response, blob_type="BlockBlob")