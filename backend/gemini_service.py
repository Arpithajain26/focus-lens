"""
Service for handling Google Gemini Generative AI operations.

This module provides summarization, flashcard generation, and
Q&A functions using the Google Gemini model.
"""

import json
import logging
import os
from typing import List, Dict

import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
if _API_KEY and _API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=_API_KEY)
_MODEL = genai.GenerativeModel('gemini-flash-latest')


def summarize_content(content: str) -> List[str]:
    """
    Summarizes the provided content into exactly 5 bullet points.

    Args:
        content (str): The text content to summarize.

    Returns:
        List[str]: A list of up to 5 summarized bullet points.
    """
    prompt: str = f"""
    You are FocusLens, an AI learning assistant. 
    Summarize the following content into exactly 5 concise, high-impact bullet points for a student.
    Content: {content}
    """
    try:
        response = _MODEL.generate_content(prompt)
        bullets: List[str] = [
            line.strip().lstrip('-').lstrip('*').strip()
            for line in response.text.strip().split('\n')
            if line.strip()
        ][:5]
        return bullets
    except Exception as e:
        logger.error("Failed to generate summary: %s", e)
        return []


def generate_flashcards(content: str) -> List[Dict[str, str]]:
    """
    Generates 5 flashcards (Question & Answer) from the provided content.

    Args:
        content (str): The text context to base questions upon.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, each containing 'question' and 'answer' keys.
    """
    prompt: str = f"""
    You are FocusLens. Generate 5 flashcards for students from the following content.
    Format your response as a valid JSON array of objects with 'question' and 'answer' keys.
    Content: {content}
    """
    try:
        response = _MODEL.generate_content(prompt)
        text: str = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        return json.loads(text)
    except Exception as e:
        logger.error("Error parsing flashcards: %s", e)
        return []


def ask_question(context: str, question: str) -> str:
    """
    Answers a follow-up question based on the provided content context.

    Args:
        context (str): The source text material.
        question (str): The user's specific question.

    Returns:
        str: The AI-generated answer.
    """
    prompt: str = f"""
    Context: {context}
    
    Student Question: {question}
    
    As FocusLens, answer the student's question based ONLY on the context provided. 
    Be concise and helpful.
    """
    try:
        response = _MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error("Failed to answer question: %s", e)
        return "I apologize, but I could not compute an answer right now."
