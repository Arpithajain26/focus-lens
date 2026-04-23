import sys
import os
import pytest
import json

# Add parent directory to path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import gemini_service
import google_services

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test that the health endpoint returns 200 OK and status healthy."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert json.loads(response.data) == {"status": "healthy"}

def test_analyze_endpoint_no_content(client):
    """Test that the analyze endpoint rejects empty content."""
    response = client.post('/api/analyze', json={'title': 'Test'})
    assert response.status_code == 400
    assert "No content provided" in json.loads(response.data)['error']

def test_analyze_endpoint_get_method_not_allowed(client):
    """Test that GET requests to analyze are rejected smoothly by our custom handler."""
    response = client.get('/api/analyze')
    assert response.status_code == 405
    assert "This endpoint only accepts POST requests" in json.loads(response.data)['error']

def test_ask_endpoint_missing_payload(client):
    """Test that the /ask api handles missing parameters gracefully."""
    response = client.post('/api/ask', json={'context': 'Only context'})
    assert response.status_code == 400
    assert "Missing context or question" in json.loads(response.data)['error']

def test_analyze_endpoint_mocked(client, mocker):
    """Test a successful analyze run by mocking the external AI APIs."""
    # Mocking Gemini Service Responses to avoid hitting live APIs during fast tests
    mocker.patch('gemini_service.summarize_content', return_value=["Point 1", "Point 2"])
    mocker.patch('gemini_service.generate_flashcards', return_value=[{"question": "Q1", "answer": "A1"}])
    
    response = client.post('/api/analyze', json={'title': 'Test Logic', 'content': 'Dummy content.'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['title'] == 'Test Logic'
    assert len(data['summary']) == 2
    assert len(data['flashcards']) == 1
    assert data['flashcards'][0]['question'] == "Q1"
