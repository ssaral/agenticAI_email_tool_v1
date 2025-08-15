# agent/functions.py

# agent/functions.py

import os
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = "assistant.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create todo table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT,
            due_date TEXT
        );
    """)

    # Create meetings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            datetime TEXT,
            attendees TEXT
        );
    """)

    conn.commit()
    conn.close()


def generate_reply(email_text: str, sender: str) -> str:
    """
    Generate a polite, context-aware reply using GPT.
    """
    system_prompt = (
        "You are an email assistant. Draft a short, professional and helpful reply to the following email:"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": email_text},
    ]
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    reply = completion.choices[0].message.content.strip()
    return reply


def schedule_meeting(datetime: str, topic: str, attendees: str):
    """
    Simulate adding a meeting by storing in SQLite.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO meetings (topic, datetime, attendees) VALUES (?, ?, ?)",
        (topic, datetime, attendees),
    )
    conn.commit()
    conn.close()
    return {"status": "scheduled", "topic": topic, "datetime": datetime}


def summarize_email(email_text: str) -> str:
    """
    Summarize the email using GPT.
    """
    prompt = f"Summarize the following email:\n\n{email_text}"
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    summary = completion.choices[0].message.content.strip()
    return summary


def add_to_todo(task: str, due_date: str):
    """
    Store tasks persistently in SQLite.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO todo (task, due_date) VALUES (?, ?)",
        (task, due_date),
    )
    conn.commit()
    conn.close()
    return {"status": "added", "task": task, "due_date": due_date}


# # Dummies for now. I need to replace these with actual implementations later.

# def generate_reply(email_text: str, sender: str):
#     print(f"[Function] generate_reply called for {sender}")
#     reply = f"Hi {sender.split('<')[0].strip()},\n\nThanks for your email!\n\nRegards,\nYour AI Assistant"
#     return reply

# def schedule_meeting(datetime: str, topic: str, attendees: str):
#     print(f"[Function] schedule_meeting called: {datetime}, {topic}, {attendees}")
#     return True

# def summarize_email(email_text: str):
#     print("[Function] summarize_email called")
#     return f"Summary: {email_text[:50]}..."

# def add_to_todo(task: str, due_date: str):
#     print(f"[Function] add_to_todo called: {task} (due {due_date})")
#     return True
