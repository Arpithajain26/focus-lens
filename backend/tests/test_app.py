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

# ==================== BASIC FUNCTIONALITY TESTS ====================

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
    """Test that GET requests to analyze are rejected smoothly."""
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

# ==================== SECURITY TESTS ====================

def test_cors_origin_validation(client):
    """Test that CORS only allows whitelisted origins."""
    # Valid origin should work
    response = client.post('/api/health', headers={'Origin': 'http://localhost:3000'})
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:3000'
    
    # Invalid origin should not be echoed back
    response = client.post('/api/health', headers={'Origin': 'http://malicious.com'})
    assert response.status_code == 200
    # Should not contain the malicious origin in CORS headers
    cors_header = response.headers.get('Access-Control-Allow-Origin', '')
    assert cors_header != 'http://malicious.com'

def test_security_headers_present(client):
    """Test that security headers are present in response."""
    response = client.get('/api/health')
    assert 'X-Content-Type-Options' in response.headers
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'X-Frame-Options' in response.headers
    assert response.headers['X-Frame-Options'] == 'DENY'

def test_analyze_invalid_json(client):
    """Test that invalid JSON is rejected."""
    response = client.post('/api/analyze', 
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400
    assert "Invalid JSON" in json.loads(response.data)['error']

def test_ask_invalid_json(client):
    """Test that /ask rejects invalid JSON."""
    response = client.post('/api/ask',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400
    assert "Invalid JSON" in json.loads(response.data)['error']

# ==================== INPUT VALIDATION TESTS ====================

def test_analyze_oversized_content(client):
    """Test that oversized content is rejected."""
    large_content = 'x' * 60000  # Exceeds MAX_CONTENT_LENGTH
    response = client.post('/api/analyze', json={'title': 'Test', 'content': large_content})
    assert response.status_code == 400
    assert "exceeds maximum length" in json.loads(response.data)['error']

def test_ask_oversized_question(client):
    """Test that oversized questions are rejected."""
    large_question = 'x' * 3000  # Exceeds MAX_QUESTION_LENGTH
    response = client.post('/api/ask', json={'context': 'context', 'question': large_question})
    assert response.status_code == 400
    assert "exceeds maximum length" in json.loads(response.data)['error']

def test_oversized_title(client, mocker):
    """Test that oversized titles are rejected."""
    mocker.patch('gemini_service.summarize_content', return_value=["Point 1"])
    mocker.patch('gemini_service.generate_flashcards', return_value=[])
    
    large_title = 'x' * 600  # Exceeds MAX_TITLE_LENGTH
    response = client.post('/api/analyze', json={'title': large_title, 'content': 'Content'})
    assert response.status_code == 400
    assert "exceeds maximum length" in json.loads(response.data)['error']

# ==================== EDGE CASE TESTS ====================

def test_analyze_empty_string_content(client):
    """Test handling of empty string content."""
    response = client.post('/api/analyze', json={'title': 'Test', 'content': ''})
    assert response.status_code == 400

def test_analyze_whitespace_only_content(client):
    """Test handling of whitespace-only content."""
    response = client.post('/api/analyze', json={'title': 'Test', 'content': '   \n\t   '})
    assert response.status_code == 400

def test_save_with_missing_fields(client):
    """Test save endpoint with missing required fields."""
    response = client.post('/api/save', json={'title': 'Test'})
    assert response.status_code == 400
    assert "Missing" in json.loads(response.data)['error']

def test_schedule_with_missing_topic(client):
    """Test schedule endpoint with missing topic."""
    response = client.post('/api/schedule', json={})
    assert response.status_code == 400
    assert "Missing" in json.loads(response.data)['error']

def test_analyze_with_none_values(client):
    """Test analyze endpoint with None values."""
    response = client.post('/api/analyze', json={'title': None, 'content': None})
    assert response.status_code == 400

def test_malformed_json_arrays(client):
    """Test handling of malformed JSON structures."""
    response = client.post('/api/ask', json={'context': [], 'question': {}})
    assert response.status_code == 400

# ==================== MOCKED INTEGRATION TESTS ====================

def test_save_endpoint_mocked(client, mocker):
    """Test save endpoint integration."""
    mocker.patch('google_services.save_to_firestore', return_value=True)
    mocker.patch('google_services.save_to_sheets', return_value=True)
    
    response = client.post('/api/save', 
                          json={'title': 'Test', 'summary': ['Point 1', 'Point 2']})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['firestore'] == True
    assert data['sheets'] == True

def test_schedule_endpoint_mocked(client, mocker):
    """Test schedule endpoint integration."""
    mocker.patch('google_services.schedule_reminder', return_value=True)
    
    response = client.post('/api/schedule', json={'topic': 'Python Basics'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True

def test_knowledge_endpoint_mocked(client, mocker):
    """Test knowledge base retrieval."""
    mock_items = [{'title': 'Item 1', 'date': '2024-01-01'}]
    mocker.patch('google_services.get_knowledge_base', return_value=mock_items)
    
    response = client.get('/api/knowledge')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['title'] == 'Item 1'

# ==================== ERROR HANDLING TESTS ====================

def test_analyze_gemini_api_error(client, mocker):
    """Test graceful handling of Gemini API failures."""
    mocker.patch('gemini_service.summarize_content', side_effect=Exception("API Error"))
    mocker.patch('gemini_service.generate_flashcards', return_value=[])
    
    response = client.post('/api/analyze', json={'title': 'Test', 'content': 'Content'})
    assert response.status_code == 500
    assert "Internal server error" in json.loads(response.data)['error']

def test_ask_gemini_failure(client, mocker):
    """Test graceful handling of gemini failure in ask endpoint."""
    mocker.patch('gemini_service.ask_question', side_effect=Exception("API Error"))
    
    response = client.post('/api/ask', json={'context': 'Context', 'question': 'Question'})
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "Internal server error" in data['error']

def test_save_firestore_error(client, mocker):
    """Test handling of Firestore save errors."""
    mocker.patch('google_services.save_to_firestore', side_effect=Exception("DB Error"))
    mocker.patch('google_services.save_to_sheets', return_value=True)
    
    response = client.post('/api/save', json={'title': 'Test', 'summary': ['Point']})
    assert response.status_code == 500
