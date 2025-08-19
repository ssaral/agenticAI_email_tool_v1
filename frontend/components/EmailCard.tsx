import React from 'react';

interface Email {
  id: string;
  threadId: string;
  from: string;
  subject: string;
  body: string;
}

type Props = {
  email: Email;
  selected: boolean;
  onSelect: () => void;
  status: 'NEW' | 'DRAFT READY' | 'SENT';
  memorySummary?: string;
};

export default function EmailCard({ email, selected, onSelect, status, memorySummary }: Props) {
  const badgeClass = status === 'NEW' ? 'new'
      : (status === 'DRAFT READY' ? 'draft' : 'sent');

  return (
    <div className={`email-card ${selected ? 'selected' : ''}`} onClick={onSelect}>
      <strong>{email.subject}</strong>
      <div>{email.from}</div>
      <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>{memorySummary || ''}</div>
      <span className={`badge ${badgeClass}`}>{status}</span>
    </div>
  );
}
