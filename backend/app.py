import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import gemini_service
import google_services
from datetime import datetime
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Simple in-memory cache for Gemini responses
analysis_cache = {}

# Restricted CORS configuration - only allow specific origins
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "https://focuslens-494202.web.app"),
    "https://focuslens-494202.web.app",
    "https://focuslens-494202.firebaseapp.com",
    "http://127.0.0.1:3000",
    "http://localhost:3000"
]

CORS(app, 
     resources={r"/*": {"origins": ALLOWED_ORIGINS}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS", "DELETE", "PUT"])

@app.after_request
def add_cors_headers(response):
    # Only echo back if origin is in whitelist
    origin = request.headers.get('Origin', '')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

# Input validation constants
MAX_CONTENT_LENGTH = 50000  # 50KB max
MAX_TITLE_LENGTH = 500
MAX_QUESTION_LENGTH = 2000

def validate_input(content, max_length):
    """Validate and sanitize user input."""
    if not content:
        return None
    if isinstance(content, str):
        content = content.strip()
    if len(str(content)) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")
    return content

@app.route('/api/analyze', methods=['GET', 'POST', 'OPTIONS'])
@limiter.limit("10 per hour")
def analyze():
    if request.method == 'GET':
        return jsonify({'error': 'This endpoint only accepts POST requests from the FocusLens frontend.'}), 405
        
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON or empty body'}), 400
        
        # Check cache
        content = data.get('content', '')
        cache_key = hash(content)
        if cache_key in analysis_cache:
            print("Serving from cache...")
            return jsonify(analysis_cache[cache_key])

        # Validate inputs
        content = validate_input(data.get('content'), MAX_CONTENT_LENGTH)
        title = validate_input(data.get('title', 'Untitled Topic'), MAX_TITLE_LENGTH)
        
        if not content:
            return jsonify({'error': 'No content provided'}), 400
            
        # Check if Gemini is configured
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("ERROR: Gemini API Key is missing or default in .env")
            return jsonify({
                'error': 'Gemini API Key is not configured. Please add it to your backend/.env file.',
                'setup_guide': 'Visit https://aistudio.google.com/app/apikey to get a free key.'
            }), 400

        import concurrent.futures

        print(f"Analyzing content for topic: {title}...")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_summary = executor.submit(gemini_service.summarize_content, content)
            future_flashcards = executor.submit(gemini_service.generate_flashcards, content)
            future_roadmap = executor.submit(gemini_service.generate_study_roadmap, content)
            
            summary = future_summary.result()
            flashcards = future_flashcards.result()
            roadmap = future_roadmap.result()
        
        # Calculate some educational metadata
        estimated_time = f"{len(content.split()) // 100 + 5} minutes"
        difficulty = "Intermediate" if len(content) > 1000 else "Foundational"

        print("Analysis complete.")
        result = {
            'title': title,
            'summary': summary,
            'flashcards': flashcards,
            'roadmap': roadmap,
            'metadata': {
                'estimated_time': estimated_time,
                'difficulty': difficulty
            }
        }
        
        # Store in cache
        analysis_cache[cache_key] = result
        
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"CRITICAL ERROR in /api/analyze: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ask', methods=['POST'])
@limiter.limit("20 per hour")
def ask():
    """
    Answers a follow-up question with input validation.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
            
        context = validate_input(data.get('context'), MAX_CONTENT_LENGTH)
        question = validate_input(data.get('question'), MAX_QUESTION_LENGTH)
        
        if not context or not question:
            return jsonify({'error': 'Missing context or question'}), 400
            
        answer = gemini_service.ask_question(context, question)
        return jsonify({'answer': answer})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"Error in /api/ask: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/save', methods=['POST'])
@limiter.limit("5 per hour")
def save():
    """
    Saves to Firestore and Google Sheets with validation.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
            
        title = validate_input(data.get('title'), MAX_TITLE_LENGTH)
        summary = validate_input(data.get('summary'), MAX_CONTENT_LENGTH)
        
        if not title or not summary:
            return jsonify({'error': 'Missing title or summary'}), 400
            
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        firestore_ok = google_services.save_to_firestore(title, summary)
        sheets_ok = google_services.save_to_sheets(title, ", ".join(summary) if isinstance(summary, list) else summary, date_str)
        
        return jsonify({
            'firestore': firestore_ok,
            'sheets': sheets_ok
        })
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"Error in /api/save: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/schedule', methods=['POST'])
@limiter.limit("5 per hour")
def schedule():
    """
    Schedules a review reminder in Google Calendar with validation.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
            
        topic = validate_input(data.get('topic'), MAX_TITLE_LENGTH)
        
        if not topic:
            return jsonify({'error': 'Missing topic'}), 400
            
        ok = google_services.schedule_reminder(topic)
        return jsonify({'success': ok})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"Error in /api/schedule: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    """
    Fetches student's knowledge base.
    """
    items = google_services.get_knowledge_base()
    return jsonify(items)

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    response = jsonify({"error": str(e)})
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', os.getenv("FRONTEND_URL", "http://localhost:3000"))
    return response, 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    # Bind to 0.0.0.0 to ensure it's accessible via both localhost and 127.0.0.1
    app.run(host='0.0.0.0', port=port, debug=True)
