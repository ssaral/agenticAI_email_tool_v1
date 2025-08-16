"""
Unified entry: launches FastAPI backend (localhost:8000) and Streamlit dashboard (localhost:8501).
"""

import os
import threading
import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel

import streamlit as st

from agent.gmail import fetch_emails
from agent.llm_agent import process_emails  # uses AUTO_SEND flag
from agent.gmail import send_email
from agent.llm_agent import get_thread_memory
from agent.gmail import fetch_thread
from agent.functions import generate_reply
from agent.gmail import get_gmail_service

import requests
from fastapi.middleware.cors import CORSMiddleware


# FASTAPI BACKEND 
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SendBody(BaseModel):
    to: str
    subject: str
    body: str

class DraftRequest(BaseModel):
    email_text: str
    sender: str

class DeleteBody(BaseModel):
    message_id: str

@app.post("/generate_draft")
def api_generate_draft(req: DraftRequest):
    draft = generate_reply(email_text=req.email_text, sender=req.sender)
    return {"draft": draft}

@app.post("/delete_email")
def delete_email(req: DeleteBody):
    service = get_gmail_service()
    service.users().messages().modify(
        userId="me", id=req.message_id,
        body={"removeLabelIds": ["INBOX"]}
    ).execute()
    return {"status": "archived"}
    
@app.get("/emails")
def get_emails():
    emails = fetch_emails(n=10)
    return emails

@app.post("/process")
def run_agent():
    emails = fetch_emails(n=5)
    process_emails(emails)
    return {"status": "done"}

@app.post("/send_reply")
def api_send_reply(payload: SendBody):
    out = send_email(to=payload.to, subject=payload.subject, body=payload.body)
    return {"status": "sent", "out": out}

@app.get("/thread/{thread_id}")
def api_thread(thread_id: str):
    messages = fetch_thread(thread_id)
    summary, last_action = get_thread_memory(thread_id)
    return {"messages": messages, "summary": summary, "last_action": last_action}


def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# STREAMLIT FRONTEND 
def start_streamlit():
    st.set_page_config(page_title="AI Email Agent", layout="wide")
    # --- Custom CSS for styling ---
    st.markdown("""
        <style>
        .email-card {
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.06);
        }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 0.75rem;
            color: white;
            margin-left: 8px;
            background-color: #14b8a6; /* teal */
        }
        .send-btn {
            background-color: #7c3aed;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
        }
        .send-btn:hover {
            background-color: #6d28d9;
        }
        /* Remove Streamlit default header/footer */
        #MainMenu {visibility:hidden;}
        footer {visibility:hidden;}

        /* Custom top bar */
        .custom-header {
            background-color:#14b8a6;
            padding:15px 10px;
            font-size:24px;
            color:white;
            font-weight:600;
            border-radius:0 0 8px 8px;
        }
        </style>

        <div class="custom-header">Saral's AI Email Agent</div>
        """, unsafe_allow_html=True)

    tabs = st.tabs(["Inbox", "Thread Memory", "Settings"])

    # TAB 1: INBOX
    with tabs[0]:
        st.header("Inbox (Unprocessed)")
        if st.button("Refresh inbox"):
            st.experimental_rerun()

        import requests
        r = requests.get("http://localhost:8000/emails")
        emails = r.json()

        for e in emails:
            with st.container():
                st.markdown(f"<div class='email-card'>", unsafe_allow_html=True)

                # Header row: Subject + From + (status)
                st.markdown(f"**{e['subject']}**  \n<small>{e['from']}</small>", unsafe_allow_html=True)

                # Body preview
                st.write(e["body"])

                # Draft controls
                if st.button("Generate GPT Draft", key=f"gptbtn_{e['id']}"):
                    from agent.functions import generate_reply
                    suggested = generate_reply(email_text=e['body'], sender=e['from'])
                    st.session_state[f"suggested_{e['id']}"] = suggested

                suggested = st.session_state.get(f"suggested_{e['id']}", "")
                if suggested:
                    st.markdown("**GPT Suggestion:**")
                    st.write(suggested)

                draft = st.text_area("Your Editable Reply",
                                    value=suggested,
                                    key=f"draft_{e['id']}")

                # Send button
                if st.button("Send from dashboard", key=f"send_{e['id']}"):
                    payload = {"to": e["from"],
                            "subject": f"Re: {e['subject']}",
                            "body": draft}
                    _ = requests.post("http://localhost:8000/send_reply", json=payload)
                    st.success("Sent!")

                st.markdown("</div>", unsafe_allow_html=True)


        # for e in emails:
        #     with st.expander(f"{e['subject']} — {e['from']}"):
        #         st.write(e["body"])
        #         # draft = st.text_area("Draft reply", "")
        #         draft = st.text_area("Draft reply", "", key=f"draft_{e['id']}")
        #         col1, col2 = st.columns(2)
        #         if col1.button("Send from dashboard", key=e['id']):
        #             payload = {"to": e["from"],
        #                        "subject": f"Re: {e['subject']}",
        #                        "body": draft}
        #             r2 = requests.post("http://localhost:8000/send_reply", json=payload)
        #             st.success("Sent!")

    # TAB 2: MEMORY
    with tabs[1]:
        st.header("Thread Memory")
        import requests
        r = requests.get("http://localhost:8000/emails")
        emails = r.json()
        for e in emails:
            memory = requests.get(f"http://localhost:8000/thread/{e['threadId']}").json()
            st.write(f"**Thread {e['threadId']}**")
            st.write("Summary:", memory['summary'])
            st.write("Last Action:", memory['last_action'])
            st.divider()

    # TAB 3: SETTINGS
    with tabs[2]:
        st.header("Agent Settings")
        if st.button("Run Agent Now"):
            requests.post("http://localhost:8000/process")
            st.success("Agent completed.")

def main():
    threading.Thread(target=start_api).start()
    start_streamlit()

if __name__ == "__main__":
    main()
