# agent/llm_agent.py
import os
import json
from typing import List, Dict

from openai import OpenAI
from dotenv import load_dotenv

from agent.functions import (
    generate_reply,
    schedule_meeting,
    summarize_email,
    add_to_todo,
    init_db,
)

from agent.gmail import send_email, mark_as_read

import sqlite3

# ------------------ Settings ------------------

AUTO_SEND = False  # set to True when you are ready to actually send emails

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_PATH = "assistant.db"

# ----------------- Persistence ------------------

def remember_email_processed(email_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS processed_emails (id TEXT PRIMARY KEY)"
    )
    cur.execute(
        "INSERT OR IGNORE INTO processed_emails (id) VALUES (?)", (email_id,)
    )
    conn.commit()
    conn.close()


def has_processed(email_id: str) -> bool:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS processed_emails (id TEXT PRIMARY KEY)"
    )
    cur.execute("SELECT 1 FROM processed_emails WHERE id=?", (email_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None


# ------------------ Tools Schema ------------------

# Describing the tools I want GPT to be able to call
FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "generate_reply",
            "description": "Generate a reply email",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_text": {"type": "string"},
                    "sender": {"type": "string"},
                },
                "required": ["email_text", "sender"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a meeting or reminder",
            "parameters": {
                "type": "object",
                "properties": {
                    "datetime": {"type": "string"},
                    "topic": {"type": "string"},
                    "attendees": {"type": "string"},
                },
                "required": ["datetime", "topic", "attendees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_email",
            "description": "Summarize the given email",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_text": {"type": "string"},
                },
                "required": ["email_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_todo",
            "description": "Add a task to a to-do list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "due_date": {"type": "string"},
                },
                "required": ["task", "due_date"],
            },
        },
    },
]


def decide_action(email: Dict):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a smart autonomous email assistant. "
                "Based on the user's email you should decide which function to call. "
                "Only respond with a function call in JSON."
            ),
        },
        {
            "role": "user",
            "content": f"Email from: {email['from']}\n"
                       f"Subject: {email['subject']}\n"
                       f"Body: {email['body']}\n"
                       "When calling functions:\n"
                        "- `email_text` should be the Body text.\n"
                        "- `sender` should be exactly the From field.\n"
                        "- If the function requires parameters not in the email, leave them as empty strings.",
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=FUNCTIONS,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        # print(f"[GPT decided to call function: {name}]")
        
        # Fill in missing parameters
        if name == "generate_reply":
            args.setdefault("email_text", email.get("body", ""))
            args.setdefault("sender", email.get("from", ""))
        elif name == "schedule_meeting":
            args.setdefault("datetime", "")
            args.setdefault("topic", "")
            args.setdefault("attendees", "")
        elif name == "summarize_email":
            args.setdefault("email_text", email.get("body", ""))
        elif name == "add_to_todo":
            args.setdefault("task", "")
            args.setdefault("due_date", "")


        # Execute local handler
        if name == "generate_reply":
            reply_text = generate_reply(**args)
            if AUTO_SEND:
                send_email(
                    to=email["from"],
                    subject=f"Re: {email['subject']}",
                    body=reply_text
                )
            print(f"[Drafted reply]\n{reply_text}\n")
            mark_as_read(email["id"])
            remember_email_processed(email["id"])
            return "reply_sent"
        elif name == "schedule_meeting":
            out = schedule_meeting(**args)
            mark_as_read(email["id"])
            remember_email_processed(email["id"])
            return str(out)
        elif name == "summarize_email":
            summary = summarize_email(**args)
            mark_as_read(email["id"])
            remember_email_processed(email["id"])
            return summary
        elif name == "add_to_todo":
            out = add_to_todo(**args)
            mark_as_read(email["id"])
            remember_email_processed(email["id"])
            return str(out)
    else:
        return "no_action"


def process_emails(emails: List[Dict]):
    for email in emails:
        if has_processed(email["id"]):
            print(f"Skipping already processed email: {email['subject']}")
            continue
        print("\n--- New Email ---")
        print("From:", email["from"])
        print("Subject:", email["subject"])
        action_output = decide_action(email)
        print("Agent Output:", action_output)
