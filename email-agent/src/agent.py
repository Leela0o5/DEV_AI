"""Email categorization and reply drafting by Gemini."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

GEMINI_MODEL = "gemini-flash-latest"

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        load_dotenv()
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set.\n"
                "Add it to your .env file or set it as an environment variable."
            )
        _client = genai.Client(api_key=key)
    return _client


# Categorization

CATEGORIZE_PROMPT = """\
You are an email triage assistant. Analyze the following emails and return a JSON array.

For each email return exactly this structure:
{{
  "id": "<email id>",
  "category": "urgent" | "action_required" | "fyi" | "newsletter",
  "summary": "<one sentence, max 100 chars>",
  "priority": <integer 1-10>,
  "needs_reply": <true|false>,
  "suggested_action": "reply" | "archive" | "label:newsletter" | "none"
}}

Category definitions:
- urgent: time-sensitive, needs attention today
- action_required: needs a response or task completion, not urgent
- fyi: informational, no action needed
- newsletter: marketing, digest, or automated bulk mail

Return ONLY the raw JSON array. No markdown fences, no explanation.

EMAILS:
{emails}
"""


def _build_email_block(emails: list[dict]) -> str:
    parts = []
    for e in emails:
        parts.append(
            f"ID: {e['id']}\n"
            f"From: {e['sender']}\n"
            f"Subject: {e['subject']}\n"
            f"Date: {e['date']}\n"
            f"Snippet: {e['snippet']}"
        )
    return "\n\n---\n\n".join(parts)


def categorize_emails(emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Send all emails to Gemini in one call and get back structured analysis.
    Returns a list of analysis dicts, one per email.
    """
    client = get_client()
    email_block = _build_email_block(emails)
    prompt = CATEGORIZE_PROMPT.format(emails=email_block)

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    raw = response.text.strip()
    raw = re.sub(r"```[a-z]*\n?", "", raw).strip()

    try:
        analyses = json.loads(raw)
        if not isinstance(analyses, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError):
        analyses = [
            {
                "id": e["id"],
                "category": "fyi",
                "summary": e["snippet"][:100],
                "priority": 5,
                "needs_reply": False,
                "suggested_action": "none",
            }
            for e in emails
        ]

    return analyses


# Reply drafting

DRAFT_PROMPT = """\
You are a professional email assistant. Draft a reply to the email below.

Guidelines:
- Be concise and professional
- Match the tone of the original email
- Do not include a subject line
- End with a polite sign-off but leave the name blank as "[Your Name]"
- Return ONLY the email body text — no explanation, no metadata

ORIGINAL EMAIL:
From: {sender}
Subject: {subject}
Body:
{body}
"""


def draft_reply(email: dict[str, Any]) -> str:
    client = get_client()
    prompt = DRAFT_PROMPT.format(
        sender=email["sender"],
        subject=email["subject"],
        body=email["body"] or email["snippet"],
    )
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip()
