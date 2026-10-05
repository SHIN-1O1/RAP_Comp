import React from 'react';

interface Props {
  answer: string | null;
  status: string;
  isLoading: boolean;
}

export const AnswerCard: React.FC<Props> = ({ answer, status, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-panel" style={{ padding: '28px', textAlign: 'center' }}>
        <div style={{
          display: 'inline-block',
          width: '36px',
          height: '36px',
          border: '3px solid rgba(99, 102, 241, 0.2)',
          borderTopColor: 'var(--primary)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          marginBottom: '16px'
        }} />
        <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
          Agent In Flight...
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Executing bounded retrieval under strict 6-call budget harness.
        </p>
        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>
      </div>
    );
  }

  if (!answer) {
    return (
      <div className="glass-panel" style={{ padding: '36px 24px', textAlign: 'center', color: 'var(--text-dim)' }}>
        <p style={{ fontSize: '14px' }}>
          Select or upload a PDF above and submit a question to begin bounded QA.
        </p>
      </div>
    );
  }

  const isInsufficient = answer.toLowerCase().includes('insufficient information');

  return (
    <div className="glass-panel animate-fade-in" style={{
      padding: '24px',
      borderLeft: `4px solid ${isInsufficient ? 'var(--warning)' : 'var(--success)'}`
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            fontSize: '12px',
            padding: '3px 10px',
            borderRadius: '999px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            background: isInsufficient ? 'var(--warning-bg)' : 'var(--success-bg)',
            color: isInsufficient ? 'var(--warning)' : 'var(--success)',
            border: `1px solid ${isInsufficient ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
          }}>
            {isInsufficient ? '⚠️ Insufficient Information' : '✓ Verified Answer'}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
            Status: <b style={{ color: 'var(--text-muted)' }}>{status}</b>
          </span>
        </div>
      </div>

      <div style={{
        whiteSpace: 'pre-wrap',
        fontSize: '15px',
        lineHeight: '1.7',
        color: 'var(--text-main)',
        background: 'rgba(10, 13, 20, 0.5)',
        padding: '16px',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-subtle)',
      }}>
        {answer}
      </div>
    </div>
  );
};
