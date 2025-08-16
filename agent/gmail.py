# agent/gmail.py

import os
import base64
from email import message_from_bytes

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.modify"]


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

        emails.append({"id": msg["id"], "threadId": msg_data["threadId"], "from": email_from, "subject": subject, "body": body})

    return emails

def fetch_thread(thread_id: str):
    """
    Returns a list of all messages in a Gmail thread, each with {from, subject, body}
    """
    service = get_gmail_service()
    thread = (
        service.users()
        .threads()
        .get(userId="me", id=thread_id, format="full")
        .execute()
    )

    messages_out = []
    for m in thread["messages"]:
        headers = m["payload"]["headers"]
        email_from = next((h["value"] for h in headers if h["name"] == "From"), "")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        body = ""

        parts = m["payload"].get("parts", [])
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    break

        messages_out.append({"from": email_from, "subject": subject, "body": body})

    return messages_out

def send_email(to: str, subject: str, body: str):
    """
    Send an email using Gmail API
    """
    service = get_gmail_service()
    message = {
        "raw": base64.urlsafe_b64encode(
            f"To:{to}\r\nSubject:{subject}\r\n\r\n{body}".encode("utf-8")
        ).decode("utf-8")
    }
    sent = (
        service.users()
        .messages()
        .send(userId="me", body=message)
        .execute()
    )
    return sent


def mark_as_read(message_id: str):
    service = get_gmail_service()
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()