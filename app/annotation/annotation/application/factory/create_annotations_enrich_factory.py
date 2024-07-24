from application.usecase.create_annotations_enrich_usecase import CreateAnnotationsEnrichUseCase

class CreateAnnotationsEnrichFactory:
    @staticmethod
    def inject_usecase(client):
        return CreateAnnotationsEnrichUseCase(client)