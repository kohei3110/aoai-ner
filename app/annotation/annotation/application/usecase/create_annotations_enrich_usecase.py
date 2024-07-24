import json
import os
import logging
from typing import Optional
from azure.core.exceptions import AzureError
from tenacity import retry, stop_after_attempt, wait_random_exponential
import wikipedia
import logging

class CreateAnnotationsEnrichUseCase:
    def __init__(self, client):
        self.client = client
        logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')
    
    def create_messages(self, text, labels, system_message, assistant_message, user_message_enrich_enable):
        messages = [
            {"role": "system", "content": system_message(labels=labels)},
            {"role": "assistant", "content": assistant_message()},
            {"role": "user", "content": user_message_enrich_enable(text)}
        ]
        return messages

    def create(self, text, labels, system_message, assistant_message, user_message_enrich_enable):
        messages = self.create_messages(text, labels, system_message, assistant_message, user_message_enrich_enable)

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("MODEL_ID"),
                messages=messages, 
                temperature=0.0,
            )
            if (response.choices[0].finish_reason == "tool_calls"):
                response.choices[0].message.content = self.enrich_entities(response.choices[0].message.tool_calls[0].function.arguments, json.loads(response.choices[0].message.tool_calls[0].function.arguments))            

            return response.choices[0].message.content
        except AzureError as e:
            logging.error(f"An error occurred: {e}")            
        
    @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
    def find_link(self, entity: str) -> Optional[str]:
        # """
        # Finds a Wikipedia link for a given entity.
        # """
        try:
            logging.info(f"Searching for Wikipedia link for entity: {entity}")
            titles = wikipedia.search(entity)
            if titles:
                # naively consider the first result as the best
                page = wikipedia.page(titles[0])
                return page.url
        except (wikipedia.exceptions.WikipediaException) as ex:
            logging.error(f'Error occurred while searching for Wikipedia link for entity {entity}: {str(ex)}')

        return None

    def find_all_links(self, label_entities:dict) -> dict:
        # """ 
        # Finds all Wikipedia links for the dictionary entities in the whitelist label list.
        # """
        whitelist = ['event', 'gpe', 'org', 'person', 'product', 'work_of_art']
        
        return {e: self.find_link(e) for label, entities in label_entities.items() 
                                for e in entities
                                if label in whitelist}


    def enrich_entities(self, text: str, label_entities: dict) -> str:
        import logging
        # """
        # Enriches text with knowledge base links.
        # """
        logging.info(f"label_entities: {label_entities}")
        entity_link_dict = self.find_all_links(label_entities)
        logging.info(f"entity_link_dict: {entity_link_dict}")
        
        for entity, link in entity_link_dict.items():
            text = text.replace(entity, f"[{entity}]({link})")

        return text