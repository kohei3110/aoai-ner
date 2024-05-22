import unittest
from unittest.mock import MagicMock
from main.application.factory.create_annotations_factory import CreateAnnotationsFactory
from main.application.usecase.create_annotations_usecase import CreateAnnotationsUseCase

class TestCreateAnnotationsFactory(unittest.TestCase):

    def test_inject_usecase(self):
        # Arrange
        mock_client = MagicMock()

        # Act
        usecase = CreateAnnotationsFactory.inject_usecase(mock_client)

        # Assert
        self.assertIsInstance(usecase, CreateAnnotationsUseCase)
        self.assertEqual(usecase.client, mock_client)

if __name__ == '__main__':
    unittest.main()