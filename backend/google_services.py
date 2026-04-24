"""
Service module for handling Google Cloud and Firebase integrations.

Includes functionality for saving to Firestore, appending to Google Sheets,
and scheduling Google Calendar reminders.
"""

import datetime
import logging
import os
from typing import List, Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Firebase Initialization
_DB: Optional[firestore.Client] = None
try:
    _cred_path: str = os.getenv("FIREBASE_KEY_PATH", "")
    if _cred_path and os.path.exists(_cred_path):
        _cred = credentials.Certificate(_cred_path)
        firebase_admin.initialize_app(_cred)
        _DB = firestore.client()
    else:
        logger.warning("Firebase credentials path missing or invalid.")
except Exception as e:
    logger.error("Firebase Init Error: %s", e)


def _get_google_credentials() -> Optional[Credentials]:
    """
    Returns Google API credentials from the service account file.
    
    Returns:
        Optional[Credentials]: Google API Credentials or None if config fails.
    """
    scopes: List[str] = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/calendar'
    ]
    cred_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
    if not cred_path or not os.path.exists(cred_path):
        logger.warning("Google credentials file not found.")
        return None
        
    return Credentials.from_service_account_file(cred_path, scopes=scopes)


def save_to_firestore(title: str, summary: List[str]) -> bool:
    """
    Saves the topic and summary to the Firebase Firestore database.

    Args:
        title (str): The topic title.
        summary (List[str]): List of summary points.

    Returns:
        bool: True if correctly saved, False otherwise.
    """
    if not _DB:
        logger.error("Firestore database is not initialized.")
        return False
    try:
        doc_ref = _DB.collection('knowledge_base').document()
        doc_ref.set({
            'title': title,
            'summary': summary,
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        })
        return True
    except Exception as e:
        logger.error("Firestore Save Error: %s", e)
        return False


def save_to_sheets(title: str, summary_str: str, date_str: str) -> bool:
    """
    Appends the entry to the configured Google Sheet.

    Args:
        title (str): Title of the context.
        summary_str (str): The stringified summary.
        date_str (str): The stringified date.

    Returns:
        bool: True if saving succeeded, False otherwise.
    """
    try:
        creds = _get_google_credentials()
        if not creds:
            return False
            
        service = build('sheets', 'v4', credentials=creds)
        spreadsheet_id: str = os.getenv("GOOGLE_SHEET_ID", "")
        if not spreadsheet_id:
            logger.error("GOOGLE_SHEET_ID is not configured in .env.")
            return False
            
        range_name: str = 'Sheet1!A:C'
        values: List[List[str]] = [[title, summary_str, date_str]]
        body: Dict[str, Any] = {'values': values}
        
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body
        ).execute()
        return True
    except Exception as e:
        logger.error("Sheets Save Error: %s", e)
        return False


def schedule_reminder(topic: str, days_from_now: int = 3) -> bool:
    """
    Creates a Google Calendar event for a future review reminder.

    Args:
        topic (str): The topic to be reviewed.
        days_from_now (int, optional): Number of days ahead. Defaults to 3.

    Returns:
        bool: True if event created successfully, False otherwise.
    """
    try:
        creds = _get_google_credentials()
        if not creds:
            return False
            
        service = build('calendar', 'v3', credentials=creds)
        
        reminder_date = datetime.datetime.now() + datetime.timedelta(days=days_from_now)
        start_time: str = reminder_date.replace(hour=9, minute=0, second=0).isoformat() + 'Z'
        end_time: str = reminder_date.replace(hour=10, minute=0, second=0).isoformat() + 'Z'
        
        event: Dict[str, Any] = {
            'summary': f'Review: {topic}',
            'description': f'FocusLens Reminder: Time to review the summaries for {topic}.',
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        
        service.events().insert(calendarId='primary', body=event).execute()
        return True
    except Exception as e:
        logger.error("Calendar Schedule Error: %s", e)
        return False


def get_knowledge_base() -> List[Dict[str, Any]]:
    """
    Fetches all entries from the Firestore database.

    Returns:
        List[Dict[str, Any]]: A list of all knowledge base document dicts.
    """
    if not _DB:
        logger.error("Firestore DB not initialized.")
        return []
    try:
        docs = _DB.collection('knowledge_base').order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error("Knowledge Base Fetch Error: %s", e)
        return []
