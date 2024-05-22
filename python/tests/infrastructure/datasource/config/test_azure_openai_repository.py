import unittest
from unittest.mock import patch, Mock
from main.infrastructure.datasource.config.azure_openai_repository import AzureOpenAIRepository

class TestAzureOpenAIRepository(unittest.TestCase):
    @patch('os.getenv')
    @patch('azure_openai_repository.AzureOpenAI')
    def test_create_openai_client(self, mock_azure_openai, mock_getenv):
        mock_getenv.side_effect = ['fake_api_key', 'fake_endpoint']
        mock_azure_openai.return_value = Mock()

        client = AzureOpenAIRepository.create_openai_client()

        mock_azure_openai.assert_called_once_with(
            api_key='fake_api_key',
            api_version='2024-02-01',
            azure_endpoint='fake_endpoint'
        )
        self.assertEqual(client, mock_azure_openai.return_value)

if __name__ == '__main__':
    unittest.main()