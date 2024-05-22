from domain.repository.annotation_repository_interface import AnnotationRepositoryInterface


class AnnotationRepository(AnnotationRepositoryInterface):
    def __init__(self, client):
        self.client = client

    def create(self, model, messages, temperature):
        return self.client.chat.completions.create(
            model=model,
            messages=messages, 
            temperature=temperature,
        )