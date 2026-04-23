import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import gemini_service
import google_services
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Restricted CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
CORS(app, resources={r"/*": {"origins": [frontend_url, "http://127.0.0.1:3000"]}})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', frontend_url)
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route('/api/analyze', methods=['GET', 'POST', 'OPTIONS'])
def analyze():
    if request.method == 'GET':
        return jsonify({'error': 'This endpoint only accepts POST requests from the FocusLens frontend.'}), 405
        
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON or empty body'}), 400
        
    content = data.get('content')
    title = data.get('title', 'Untitled Topic')
    
    if not content:
        return jsonify({'error': 'No content provided'}), 400
        
    try:
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
            
            summary = future_summary.result()
            flashcards = future_flashcards.result()
        
        print("Analysis complete.")
        return jsonify({
            'title': title,
            'summary': summary,
            'flashcards': flashcards
        })
    except Exception as e:
        print(f"CRITICAL ERROR in /api/analyze: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask():
    """
    Answers a follow-up question.
    """
    data = request.json
    context = data.get('context')
    question = data.get('question')
    
    if not context or not question:
        return jsonify({'error': 'Missing context or question'}), 400
        
    try:
        answer = gemini_service.ask_question(context, question)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save():
    """
    Saves to Firestore and Google Sheets.
    """
    data = request.json
    title = data.get('title')
    summary = data.get('summary')
    
    if not title or not summary:
        return jsonify({'error': 'Missing title or summary'}), 400
        
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    firestore_ok = google_services.save_to_firestore(title, summary)
    sheets_ok = google_services.save_to_sheets(title, ", ".join(summary), date_str)
    
    return jsonify({
        'firestore': firestore_ok,
        'sheets': sheets_ok
    })

@app.route('/api/schedule', methods=['POST'])
def schedule():
    """
    Schedules a review reminder in Google Calendar.
    """
    data = request.json
    topic = data.get('topic')
    
    if not topic:
        return jsonify({'error': 'Missing topic'}), 400
        
    ok = google_services.schedule_reminder(topic)
    return jsonify({'success': ok})

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
