import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_get_index():
    # Make sure we don't accidentally fail if env var is missing during test
    os.environ["GOOGLE_MAPS_API_KEY"] = "TEST_MAPS_KEY"
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "TEST_MAPS_KEY" in response.text

@patch("main.genai.GenerativeModel")
def test_chat_valid(mock_gen_model):
    # Setup mock response
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked AI Response"
    mock_instance.generate_content.return_value = mock_response
    mock_gen_model.return_value = mock_instance

    payload = {"message": "Hello", "system_prompt": "Test prompt"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"response": "Mocked AI Response"}
    
    # Verify the mock was called with the combined prompt
    mock_instance.generate_content.assert_called_once_with("Test prompt\n\nUser: Hello")

def test_chat_invalid():
    # Missing message
    payload = {"system_prompt": "Test prompt"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422

@patch("main.genai.GenerativeModel")
def test_chat_exception(mock_gen_model):
    # Setup mock to raise an exception
    mock_instance = MagicMock()
    mock_instance.generate_content.side_effect = Exception("API Quota Exceeded")
    mock_gen_model.return_value = mock_instance

    payload = {"message": "Hello", "system_prompt": "Test"}
    response = client.post("/chat", json=payload)
    
    # The application catches the exception and raises a 500
    assert response.status_code == 500
    assert "The AI is currently resetting. Please try again." in response.json()["detail"]
