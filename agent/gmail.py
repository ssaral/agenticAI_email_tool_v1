# agent/gmail.py

import os
import base64
from email import message_from_bytes

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    token_path = "token.json"

    # If token exists, use it
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid creds -> OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def fetch_emails(n=5):
    """Fetch last n unread emails"""
    service = get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["UNREAD"], maxResults=n)
        .execute()
    )

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_data = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        payload = msg_data["payload"]
        headers = payload["headers"]

        email_from = next(
            (h["value"] for h in headers if h["name"] == "From"), None
        )
        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"), None
        )

        parts = payload.get("parts", [])
        body = ""
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                break

        emails.append({"from": email_from, "subject": subject, "body": body})

    return emails
