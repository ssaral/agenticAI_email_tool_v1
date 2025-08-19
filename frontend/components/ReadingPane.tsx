import axios from "axios";
import React, { useState } from "react";
import { Email } from "./types";

type Props = {
  email: Email;
}

export default function ReadingPane({ email }: Props) {
  const [draft, setDraft] = useState('');
  const [suggested, setSuggested] = useState('');

  if (!email) {
    return <div>Select an email to view details.</div>
  }

  async function generateDraft() {
    const res = await axios.post('http://localhost:8000/generate_draft', {
      email_text: email.body,
      sender: email.from
    });
    setSuggested(res.data.draft);
    setDraft(res.data.draft);
  }

  async function send() {
    await axios.post('http://localhost:8000/send_reply', {
      to: email.from,
      subject: `Re: ${email.subject}`,
      body: draft
    });
    alert("Sent!");
  }

  async function del() {
    await axios.post('http://localhost:8000/delete_email', {
      message_id: email.id
    });
    alert("Archived");
  }

  return (
    <div>
      <h3>{email.subject}</h3>
      <h4>{email.from}</h4>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{email.body}</pre>

      <button onClick={generateDraft}>Generate GPT Draft</button>
      {suggested && (
        <>
          <h4>Suggestion:</h4>
          <pre>{suggested}</pre>
          <textarea value={draft} onChange={e => setDraft(e.target.value)} rows={8} style={{ width: '100%' }} />
          <button onClick={send}>Send</button>
          <button onClick={del}>Delete</button>
        </>
      )}
    </div>
  );
}
