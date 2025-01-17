from fastapi.testclient import TestClient
from app.search.aisearch.main import app
from unittest.mock import patch

def test_fulltext():
    client = TestClient(app)
    mock_response = [{"sourcepage": "test_page", "content": "test_content"}]
    with patch("app.search.aisearch.main.execute_fulltext_search", return_value=mock_response):
        response = client.get("/fulltext", params={"query": "test"})
    assert response.status_code == 200
    assert response.json() == mock_response
