import os
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase Initialization
try:
    cred = credentials.Certificate(os.getenv("FIREBASE_KEY_PATH"))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase Init Error: {e}")
    db = None

def get_google_credentials():
    """
    Returns Google API credentials from the service account file.
    """
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/calendar'
    ]
    return Credentials.from_service_account_file(
        os.getenv("GOOGLE_CREDENTIALS_PATH"), scopes=scopes
    )

def save_to_firestore(title, summary):
    """
    Saves the topic and summary to Firestore.
    """
    if not db:
        return False
    try:
        doc_ref = db.collection('knowledge_base').document()
        doc_ref.set({
            'title': title,
            'summary': summary,
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        })
        return True
    except Exception as e:
        print(f"Firestore Save Error: {e}")
        return False

def save_to_sheets(title, summary, date_str):
    """
    Appends the entry to a Google Sheet.
    """
    try:
        creds = get_google_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # You'll need to specify a Spreadsheet ID in .env
        spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
        range_name = 'Sheet1!A:C'
        
        values = [[title, summary, date_str]]
        body = {'values': values}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body).execute()
        return True
    except Exception as e:
        print(f"Sheets Save Error: {e}")
        return False

def schedule_reminder(topic, days_from_now=3):
    """
    Creates a Google Calendar event for a review reminder.
    """
    try:
        creds = get_google_credentials()
        service = build('calendar', 'v3', credentials=creds)
        
        reminder_date = datetime.datetime.now() + datetime.timedelta(days=days_from_now)
        start_time = reminder_date.replace(hour=9, minute=0, second=0).isoformat() + 'Z'
        end_time = reminder_date.replace(hour=10, minute=0, second=0).isoformat() + 'Z'
        
        event = {
            'summary': f'Review: {topic}',
            'description': f'FocusLens Reminder: Time to review the summaries for {topic}.',
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        
        service.events().insert(calendarId='primary', body=event).execute()
        return True
    except Exception as e:
        print(f"Calendar Schedule Error: {e}")
        return False

def get_knowledge_base():
    """
    Fetches all entries from Firestore.
    """
    if not db:
        return []
    try:
        docs = db.collection('knowledge_base').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Knowledge Base Fetch Error: {e}")
        return []
