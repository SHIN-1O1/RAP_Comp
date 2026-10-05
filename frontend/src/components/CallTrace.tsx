import React from 'react';
import type { CallRecord } from '../types';

interface Props {
  trace: CallRecord[];
  maxCalls: number;
}

export const CallTrace: React.FC<Props> = ({ trace, maxCalls = 6 }) => {
  if (!trace || trace.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>⏱️</span> Execution Call Trace (Harness Audit)
        </h3>
        <span style={{ fontSize: '11px', color: 'var(--text-dim)', background: 'var(--bg-secondary)', padding: '3px 8px', borderRadius: '4px' }}>
          Strictly bounded: max {maxCalls} pre-final calls
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {trace.map((record, idx) => {
          const isFinal = record.call_type === 'final_answer';
          const isError = !record.success;

          return (
            <div
              key={idx}
              style={{
                display: 'grid',
                gridTemplateColumns: '90px 140px 1fr 90px',
                gap: '12px',
                alignItems: 'center',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                background: isFinal
                  ? 'rgba(168, 85, 247, 0.1)'
                  : isError
                  ? 'var(--danger-bg)'
                  : 'rgba(10, 13, 20, 0.5)',
                border: `1px solid ${
                  isFinal
                    ? 'rgba(168, 85, 247, 0.3)'
                    : isError
                    ? 'rgba(239, 68, 68, 0.3)'
                    : 'var(--border-subtle)'
                }`,
                fontSize: '13px',
              }}
            >
              {/* Call Number / Badge */}
              <div>
                {isFinal ? (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    background: 'var(--primary-gradient)',
                    color: '#fff',
                    textTransform: 'uppercase',
                  }}>
                    FINAL
                  </span>
                ) : (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-muted)',
                    border: '1px solid var(--border-subtle)',
                  }}>
                    Call {record.call_number}/{maxCalls}
                  </span>
                )}
              </div>

              {/* Tool / Component Name */}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontWeight: 600, color: isFinal ? '#c084fc' : 'var(--text-main)', fontFamily: 'monospace' }}>
                  {record.tool_name}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                  {record.call_type}
                </span>
              </div>

              {/* Summary & Args */}
              <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                <span style={{ color: 'var(--text-muted)' }}>{record.result_summary}</span>
                {Object.keys(record.arguments || {}).length > 0 && (
                  <span style={{ color: 'var(--text-dim)', marginLeft: '8px', fontSize: '11px', fontFamily: 'monospace' }}>
                    {JSON.stringify(record.arguments)}
                  </span>
                )}
              </div>

              {/* Latency & Budget */}
              <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--accent-cyan)', fontSize: '12px', fontFamily: 'monospace' }}>
                  {record.duration_ms} ms
                </span>
                {!isFinal && (
                  <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                    rem: {record.budget_remaining}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
