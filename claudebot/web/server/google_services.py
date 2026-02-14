"""Google Services integration for Mimi — Gmail, Calendar, and Drive/Docs."""

import os
import base64
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes Mimi needs
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]

_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(_DIR, "google_credentials.json")
TOKEN_FILE = os.path.join(_DIR, "google_token.json")


def _write_env_json_to_file(env_var, file_path):
    """If env var exists but file doesn't, write env var contents to file."""
    if not os.path.exists(file_path):
        raw = os.environ.get(env_var, "").strip()
        if raw:
            with open(file_path, "w") as f:
                f.write(raw)


def get_credentials():
    """Load or refresh Google OAuth credentials."""
    # On Railway, write env vars to files if files don't exist
    _write_env_json_to_file("GOOGLE_CREDENTIALS_JSON", CREDS_FILE)
    _write_env_json_to_file("GOOGLE_TOKEN_JSON", TOKEN_FILE)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Persist refreshed token back to file and env
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(
                    f"Google credentials not found at {CREDS_FILE}. "
                    "Run google_auth.py first or set GOOGLE_CREDENTIALS_JSON env var."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
    return creds


def _gmail():
    return build("gmail", "v1", credentials=get_credentials())


def _calendar():
    return build("calendar", "v3", credentials=get_credentials())


def _drive():
    return build("drive", "v3", credentials=get_credentials())


def _docs():
    return build("docs", "v1", credentials=get_credentials())


# ── Gmail ────────────────────────────────────────────────────

def gmail_check_inbox(max_results=5, query="is:unread"):
    """Check inbox for recent messages."""
    service = _gmail()
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        return "No messages found."

    summaries = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        summaries.append({
            "id": msg_meta["id"],
            "from": headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return summaries


def gmail_read_message(message_id):
    """Read a full email message by ID."""
    service = _gmail()
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    # Extract body
    body = ""
    payload = msg.get("payload", {})
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                break
    elif "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    return {
        "from": headers.get("From", "Unknown"),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date": headers.get("Date", ""),
        "body": body,
    }


def gmail_send(to, subject, body, html=False):
    """Send an email."""
    service = _gmail()
    if html:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body, "html"))
    else:
        message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return f"Email sent (ID: {sent['id']})"


def gmail_reply(message_id, body):
    """Reply to an existing email thread."""
    service = _gmail()
    original = service.users().messages().get(
        userId="me", id=message_id, format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"]
    ).execute()
    headers = {h["name"]: h["value"] for h in original.get("payload", {}).get("headers", [])}

    reply = MIMEText(body)
    reply["to"] = headers.get("From", "")
    reply["subject"] = "Re: " + headers.get("Subject", "")
    reply["In-Reply-To"] = headers.get("Message-ID", "")
    reply["References"] = headers.get("Message-ID", "")

    raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
    sent = service.users().messages().send(
        userId="me", body={"raw": raw, "threadId": original.get("threadId")}
    ).execute()
    return f"Reply sent (ID: {sent['id']})"


# ── Calendar ─────────────────────────────────────────────────

def calendar_list_events(days_ahead=7, max_results=10):
    """List upcoming calendar events."""
    service = _calendar()
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

    results = service.events().list(
        calendarId="primary", timeMin=time_min, timeMax=time_max,
        maxResults=max_results, singleEvents=True, orderBy="startTime"
    ).execute()
    events = results.get("items", [])
    if not events:
        return "No upcoming events."

    summaries = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        summaries.append({
            "id": event["id"],
            "summary": event.get("summary", "(no title)"),
            "start": start,
            "end": event["end"].get("dateTime", event["end"].get("date")),
            "location": event.get("location", ""),
            "description": event.get("description", ""),
        })
    return summaries


def calendar_create_event(summary, start_time, end_time, description="", location="", attendees=None):
    """Create a calendar event.

    start_time/end_time: ISO format strings like '2026-02-15T10:00:00-06:00'
    attendees: list of email strings
    """
    service = _calendar()
    event = {
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    if description:
        event["description"] = description
    if location:
        event["location"] = location
    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: {created.get('summary')} on {created['start'].get('dateTime', created['start'].get('date'))} (ID: {created['id']})"


def calendar_delete_event(event_id):
    """Delete a calendar event by ID."""
    service = _calendar()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"Event {event_id} deleted."


# ── Google Drive / Docs ──────────────────────────────────────

def docs_create(title, body_text=""):
    """Create a new Google Doc and optionally insert text."""
    docs_service = _docs()
    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

    if body_text:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": body_text}}]}
        ).execute()

    return {"id": doc_id, "title": title, "url": doc_url}


def docs_read(document_id):
    """Read the text content of a Google Doc."""
    docs_service = _docs()
    doc = docs_service.documents().get(documentId=document_id).execute()
    title = doc.get("title", "")

    # Extract text from document body
    text = ""
    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            for run in element["paragraph"].get("elements", []):
                if "textRun" in run:
                    text += run["textRun"]["content"]

    return {"id": document_id, "title": title, "text": text}


def docs_append(document_id, text):
    """Append text to the end of a Google Doc."""
    docs_service = _docs()
    doc = docs_service.documents().get(documentId=document_id).execute()
    # Find end of document
    end_index = doc["body"]["content"][-1]["endIndex"] - 1

    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={"requests": [{"insertText": {"location": {"index": end_index}, "text": text}}]}
    ).execute()
    return f"Text appended to document {document_id}."


def drive_list_files(query="", max_results=10):
    """List files in Google Drive."""
    service = _drive()
    q = query or "trashed=false"
    results = service.files().list(
        q=q, pageSize=max_results,
        fields="files(id, name, mimeType, modifiedTime, webViewLink)"
    ).execute()
    files = results.get("files", [])
    if not files:
        return "No files found."
    return [
        {
            "id": f["id"],
            "name": f["name"],
            "type": f["mimeType"],
            "modified": f.get("modifiedTime", ""),
            "url": f.get("webViewLink", ""),
        }
        for f in files
    ]


# ── Convenience for Mimi ────────────────────────────────────

def google_status():
    """Check if Google services are authenticated."""
    try:
        creds = get_credentials()
        return {"authenticated": True, "email": "msmimibot2@gmail.com", "scopes": SCOPES}
    except Exception as e:
        return {"authenticated": False, "error": str(e)}
