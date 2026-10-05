import React from 'react';

interface Props {
  callsUsed: number;
  maxCalls: number;
}

export const BudgetGauge: React.FC<Props> = ({ callsUsed, maxCalls = 6 }) => {
  const remaining = Math.max(0, maxCalls - callsUsed);

  return (
    <div style={{
      background: 'rgba(16, 21, 34, 0.8)',
      padding: '16px 20px',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      gap: '10px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Pre-Final Call Budget
          </span>
          <span style={{
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '999px',
            background: callsUsed >= maxCalls ? 'var(--danger-bg)' : 'var(--primary-bg)',
            color: callsUsed >= maxCalls ? 'var(--danger)' : 'var(--primary)',
            fontWeight: 600,
            border: `1px solid ${callsUsed >= maxCalls ? 'rgba(239, 68, 68, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`
          }}>
            {callsUsed >= maxCalls ? 'BUDGET EXHAUSTED' : `${remaining} AVAILABLE`}
          </span>
        </div>
        <div style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, fontSize: '18px', color: 'var(--text-main)' }}>
          <span style={{ color: callsUsed > 4 ? 'var(--warning)' : 'var(--accent-cyan)' }}>{callsUsed}</span>
          <span style={{ color: 'var(--text-dim)', margin: '0 3px' }}>/</span>
          <span>{maxCalls}</span>
        </div>
      </div>

      {/* Segmented Budget Indicator */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${maxCalls}, 1fr)`, gap: '6px', height: '10px' }}>
        {Array.from({ length: maxCalls }).map((_, index) => {
          const isFilled = index < callsUsed;
          let segmentColor = 'rgba(255, 255, 255, 0.08)';
          if (isFilled) {
            if (index < 4) segmentColor = 'linear-gradient(135deg, #06b6d4, #6366f1)';
            else if (index < 5) segmentColor = 'linear-gradient(135deg, #6366f1, #f59e0b)';
            else segmentColor = 'linear-gradient(135deg, #f59e0b, #ef4444)';
          }
          return (
            <div
              key={index}
              style={{
                borderRadius: '4px',
                background: segmentColor,
                transition: 'all 0.3s ease',
                boxShadow: isFilled ? '0 0 8px rgba(99, 102, 241, 0.3)' : 'none'
              }}
              title={`Call slot ${index + 1}`}
            />
          );
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-dim)' }}>
        <span>Call 1: LLM Planner</span>
        <span>Calls 2-6: Document Tools</span>
        <span>Final Answer: Separate Call</span>
      </div>
    </div>
  );
};
