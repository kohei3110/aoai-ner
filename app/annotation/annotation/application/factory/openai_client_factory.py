from abc import ABCMeta, abstractmethod

class OpenAIClientFactory(metaclass=ABCMeta):
    @abstractmethod
    def create_openai_client(self):
        pass