# main.py

from agent.gmail import fetch_emails
from agent.llm_agent import process_emails

if __name__ == "__main__":
    emails = fetch_emails(n=1)
    # for e in emails:
    #     print("-" * 50)
    #     print("From:", e["from"])
    #     print("Subject:", e["subject"])
    #     print("Body:", e["body"])
    
    process_emails(emails)

