import React, { useState } from 'react';
import type { EvidenceItem } from '../types';

interface Props {
  evidence: EvidenceItem[];
}

export const EvidenceList: React.FC<Props> = ({ evidence }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  if (!evidence || evidence.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>📑</span> Retrieved Document Evidence ({evidence.length} page{evidence.length === 1 ? '' : 's'})
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {evidence.map((item, idx) => {
          const isExpanded = expandedIndex === idx;
          const isSuperseding = item.relation === 'SUPERSEDES';

          return (
            <div
              key={idx}
              style={{
                background: 'rgba(10, 13, 20, 0.4)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden',
                transition: 'all 0.2s',
              }}
            >
              <div
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                style={{
                  padding: '10px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  background: isExpanded ? 'rgba(255, 255, 255, 0.03)' : 'transparent',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    background: 'var(--bg-secondary)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    color: 'var(--text-main)',
                    border: '1px solid var(--border-subtle)',
                  }}>
                    Page {item.page_number}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontWeight: 600,
                    background: isSuperseding ? 'var(--warning-bg)' : 'var(--primary-bg)',
                    color: isSuperseding ? 'var(--warning)' : 'var(--primary)',
                  }}>
                    {item.relation}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    {item.relevance}
                  </span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                  {isExpanded ? '▲ Hide' : '▼ View'}
                </span>
              </div>

              {isExpanded && (
                <div style={{
                  padding: '14px',
                  borderTop: '1px solid var(--border-subtle)',
                  fontSize: '13px',
                  color: 'var(--text-muted)',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '260px',
                  overflowY: 'auto',
                  fontFamily: 'monospace',
                  background: 'rgba(0, 0, 0, 0.25)',
                }}>
                  {item.content}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
