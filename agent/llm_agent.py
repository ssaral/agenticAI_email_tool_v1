# agent/llm_agent.py

import os
import json
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI

from agent.functions import (
    generate_reply,
    schedule_meeting,
    summarize_email,
    add_to_todo,
)

from agent.gmail import fetch_thread, send_email, mark_as_read

# Settings
AUTO_SEND = True          # flip to True to actually send emails
SUMMARY_SENTENCE_MAX = 4   # max sentences in thread summary


# Init
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = "assistant.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            thread_id TEXT PRIMARY KEY,
            summary TEXT,
            last_action TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_thread_memory(thread_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT summary, last_action FROM threads WHERE thread_id=?", (thread_id,))
    row = cur.fetchone()
    conn.close()
    return row if row else (None, None)


def update_thread_memory(thread_id: str, summary: str, last_action: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO threads (thread_id, summary, last_action)
        VALUES (?, ?, ?)
        ON CONFLICT(thread_id) DO UPDATE SET summary=?, last_action=?
    """, (thread_id, summary, last_action, summary, last_action))
    conn.commit()
    conn.close()

#  Tools Schema

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

def decide_action(email):
    """
    Decides the next function call (if any) using GPT-4 function calling.
    Includes past thread memory if present.
    """
    thread_id = email["threadId"]
    previous_summary, previous_action = get_thread_memory(thread_id)

    system_prompt = (
        "You are an autonomous email assistant. Based on the user's email you should "
        "decide which function to call. Only respond with a function call in JSON. "
    )

    if previous_summary:
        system_prompt += (
            f"Here is the previous conversation summary: {previous_summary}. "
            f"Last action taken was: {previous_action}. "
            "Only act if new email requires a new action."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Email from: {email['from']}\n"
                                    # f"Subject: {email['subject']}\n" # Only the latest incoming message body is passed to GPT for deciding next action
                                    f"Body: {email['body']}"},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=FUNCTIONS,
        tool_choice="auto",
    )

    message = response.choices[0].message
    if not message.tool_calls:
        return "no_action", None

    tool_call = message.tool_calls[0]
    fn_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    # Fill in missing parameters
    if fn_name == "generate_reply":
        arguments.setdefault("email_text", email.get("body", ""))
        arguments.setdefault("sender", email.get("from", ""))
    elif fn_name == "schedule_meeting":
        arguments.setdefault("datetime", "")
        arguments.setdefault("topic", "")
        arguments.setdefault("attendees", "")
    elif fn_name == "summarize_email":
        arguments.setdefault("email_text", email.get("body", ""))
    elif fn_name == "add_to_todo":
        arguments.setdefault("task", "")
        arguments.setdefault("due_date", "")

    if fn_name == "generate_reply":
        reply = generate_reply(**arguments)
        if AUTO_SEND:
            send_email(to=email["from"], subject=f"Re: {email['subject']}", body=reply)
            print("Sent email.")
        print("[Draft reply]\n", reply)
        mark_as_read(email["id"])
        return "reply_sent", reply

    elif fn_name == "schedule_meeting":
        out = schedule_meeting(**arguments)
        mark_as_read(email["id"])
        return "scheduled_meeting", str(out)

    elif fn_name == "summarize_email":
        s = summarize_email(**arguments)
        mark_as_read(email["id"])
        return "summarized", s

    elif fn_name == "add_to_todo":
        out = add_to_todo(**arguments)
        mark_as_read(email["id"])
        return "todo_added", str(out)

    return "no_action", None


def get_new_thread_summary(full_thread_messages, max_sentences=4):
    """
    GPT call to compress entire conversation thread into N sentences.
    """
    thread_text = "\n\n".join(
        [f"From: {m['from']}\n{m['body']}" for m in full_thread_messages]
    )

    messages = [
        {"role": "system", "content": f"Summarize this conversation in at most {max_sentences} sentences."},
        {"role": "user", "content": thread_text},
    ]
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return completion.choices[0].message.content.strip()


def process_emails(emails):
    for email in emails:
        thread_id = email["threadId"]

        print("\n--- New Email ---")
        print("From:", email["from"])
        print("Subject:", email["subject"])

        action_taken, agent_output = decide_action(email)
        print("Action:", action_taken)

        if action_taken != "no_action":
            full_thread = fetch_thread(thread_id)
            summary = get_new_thread_summary(full_thread, SUMMARY_SENTENCE_MAX)
            update_thread_memory(thread_id, summary, action_taken)
            print("Memory updated:", summary)
        else:
            print("No action needed. (Possibly redundant message)")
