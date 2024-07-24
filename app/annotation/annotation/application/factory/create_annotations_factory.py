from application.usecase.create_annotations_usecase import CreateAnnotationsUseCase


class CreateAnnotationsFactory:    
    @staticmethod
    def inject_usecase(client):
        return CreateAnnotationsUseCase(client)