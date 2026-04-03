"""Gmail API authentication and all inbox/mail operations."""

from __future__ import annotations

import base64
import email as email_lib
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

TOKEN_FILE = Path("token.json")
CREDENTIALS_FILE = Path("credentials.json")


def authenticate():
    """
    Run OAuth2 flow and return an authenticated Gmail service.
    On first run this opens a browser window to grant access.
    After that, the token is saved to token.json and reused automatically.
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json not found.\n"
                    "Download it from Google Cloud Console:\n"
                    "  APIs & Services → Credentials → OAuth 2.0 Client → Download JSON\n"
                    "Then place it in the project root as 'credentials.json'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Extract plain-text body from a Gmail message payload."""
    # Single-part message
    if "body" in payload and payload["body"].get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Multipart - find text/plain first, fall back to text/html
    parts = payload.get("parts", [])
    for mime_type in ("text/plain", "text/html"):
        for part in parts:
            if part.get("mimeType") == mime_type and part.get("body", {}).get("data"):
                data = part["body"]["data"]
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return ""


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_emails(service, max_results: int = 20) -> list[dict[str, Any]]:
    """
    Fetch the most recent emails from the inbox.
    Returns a list of dicts with: id, thread_id, subject, sender,
    date, snippet, body ( 3000 chars).
    """
    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results,
    ).execute()

    message_refs = result.get("messages", [])
    emails = []

    for ref in message_refs:
        msg = service.users().messages().get(
            userId="me",
            id=ref["id"],
            format="full",
        ).execute()

        headers = msg["payload"].get("headers", [])
        body = _decode_body(msg["payload"])

        emails.append({
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "subject": _header(headers, "subject") or "(no subject)",
            "sender": _header(headers, "from"),
            "date": _header(headers, "date"),
            "snippet": msg.get("snippet", ""),
            "body": body[:3000],  # cap at 3000 chars to keep LLM context manageable
        })

    return emails


def send_reply(service, thread_id: str, to: str, subject: str, body: str) -> None:
    """Send a reply within an existing thread."""
    mime = MIMEText(body)
    mime["to"] = to
    mime["subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": thread_id},
    ).execute()


def archive_message(service, message_id: str) -> None:
    """Remove the INBOX label from a message (archive it)."""
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["INBOX"]},
    ).execute()


def apply_label(service, message_id: str, label_name: str) -> None:
    """Apply a label to a message, creating the label first if it doesn't exist."""
    # Fetch existing labels
    existing = service.users().labels().list(userId="me").execute().get("labels", [])
    label_id = next((l["id"] for l in existing if l["name"] == label_name), None)

    # Create label if missing
    if not label_id:
        created = service.users().labels().create(
            userId="me",
            body={"name": label_name},
        ).execute()
        label_id = created["id"]

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id]},
    ).execute()
