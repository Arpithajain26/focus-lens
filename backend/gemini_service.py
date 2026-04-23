import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key and api_key != "your_gemini_api_key_here":
    genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

def summarize_content(content):
    """
    Summarizes the provided content into 5 bullet points.
    """
    prompt = f"""
    You are FocusLens, an AI learning assistant. 
    Summarize the following content into exactly 5 concise, high-impact bullet points for a student.
    Content: {content}
    """
    response = model.generate_content(prompt)
    # Split by lines and clean
    bullets = [line.strip().lstrip('-').lstrip('*').strip() for line in response.text.strip().split('\n') if line.strip()][:5]
    return bullets

def generate_flashcards(content):
    """
    Generates 5 flashcards (Question & Answer) from the content.
    Returns a list of dicts: [{'question': '...', 'answer': '...'}]
    """
    prompt = f"""
    You are FocusLens. Generate 5 flashcards for students from the following content.
    Format your response as a valid JSON array of objects with 'question' and 'answer' keys.
    Content: {content}
    """
    response = model.generate_content(prompt)
    import json
    try:
        # Extract JSON if wrapped in markdown
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing flashcards: {e}")
        return []

def ask_question(context, question):
    """
    Answers a follow-up question based on the provided content context.
    """
    prompt = f"""
    Context: {context}
    
    Student Question: {question}
    
    As FocusLens, answer the student's question based ONLY on the context provided. 
    Be concise and helpful.
    """
    response = model.generate_content(prompt)
    return response.text.strip()
