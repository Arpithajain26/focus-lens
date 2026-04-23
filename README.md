# FocusLens: Master Knowledge With Velocity

FocusLens is an AI-powered learning and intelligence assistant that transforms dense, overloaded reading materials into structured neural sets, optimized for cognitive retention and focus.

## 🎯 Chosen Vertical
**Education & Information Overload Management**
FocusLens is designed to serve as a smart, dynamic assistant for students, researchers, and professionals who deal with overwhelming amounts of textual data. It seamlessly resolves information overload by synthesizing content into high-impact insights and interactive flashcards.

## 🧠 Approach & Logic
Our logic is driven by the principle of **Active Recall** and **Cognitive Velocity**.
When a user inputs dense text (either through typing or using the built-in Voice-to-Text capability), FocusLens evaluates the context and makes dynamic decisions on how to structure it:
1. It uses a parallel-processed approach to query standard constraints via the Gemini API.
2. It generates a Top-5 Intelligence Map (Key Insights) while simultaneously crafting contextual Flashcards.
3. Users can dynamically follow up with specific Q&A based solely on the provided context, preventing hallucination by keeping Gemini strictly contained to the uploaded text bounds.
4. The system is heavily integrated with Google Workspace and Firebase to give the user persistent control over their learning.

## ⚙️ How the Solution Works
FocusLens is a Full-Stack application comprising a React/Vite Frontend and a Python/Flask Backend.

1. **Processing**: The user inputs text or speech on the client side. The React UI sends a secure API call to the Flask backend.
2. **Gemini Engine**: The Python server relays the information to `gemini-flash-latest`, running two threaded tasks (Summarization + Flashcard Generation) for rapid execution.
3. **Interactive Study Room**: The user's screen transitions to an active study session. They can use Text-to-Speech to read aloud insights or engage with the flashcards.
4. **Google Services Integration**:
    - **Google Gemini API**: Core NLP processing.
    - **Firebase Firestore**: Users can invoke `/api/save` directly from the interface to save their session into a cloud database.
    - **Google Sheets API**: Concurrently stores summaries into a spreadsheet for organized, tabular record-keeping.
    - **Google Calendar API**: Users can click "Schedule Review" to interact with the backend `/api/schedule`, which automatically sets up a review reminder 3 days out in their primary Google Calendar.

## 📌 Assumptions Made
- **Local Execution:** We safely assume the Flask backend runs on Localhost (`:5000`) and Vite runs on Localhost (`:3000`). Aggressive CORS configuration is intentionally restricted down to the client domain to respect security requirements.
- **Service Keys Presence:** For Firebase and Google Cloud functionalities to properly work out-of-the-box, it is assumed the evaluator provides their own `firebase-key.json`, `google-credentials.json` and a Gemini API key within the local `.env` setup mapping to `GEMINI_API_KEY`, `FIREBASE_KEY_PATH`, and `GOOGLE_CREDENTIALS_PATH`. Testing environment runs efficiently avoiding complete failures even if Google credentials aren't loaded, thanks to explicit exception handling scopes.

## 🛠 Prerequisites for Local Build
- `.env` configuring keys and ports.
- `npm install` inside `/client`
- `pip install -r requirements.txt` inside `/backend`
- Tests run gracefully under PyTest (`pytest backend/tests/test_app.py`).
