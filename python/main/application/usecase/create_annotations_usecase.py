import os
import logging
from azure.core.exceptions import AzureError
from azure.functions import HttpResponse

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
            return HttpResponse(response.choices[0].message.content, status_code=200)
        except AzureError as e:
            logging.error(f"An error occurred: {e}")
            return HttpResponse(None, status_code=500)