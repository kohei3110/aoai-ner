from abc import ABC, abstractmethod

class AnnotationRepositoryInterface(ABC):
    @abstractmethod
    def create(self, model, messages, temperature):
        pass