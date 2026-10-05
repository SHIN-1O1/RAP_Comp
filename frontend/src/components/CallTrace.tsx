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

  const getDisplayName = (record: CallRecord) => {
    if (record.call_type === 'final_answer') return 'Final Answer';
    if (record.call_type === 'llm_planning') return 'LLM Planner';
    if (record.tool_name === 'search_keyword') return 'Document Search';
    if (record.tool_name === 'get_page') return 'Document Page';
    if (record.tool_name === 'list_headings') return 'Document Headings';
    return record.tool_name;
  };

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
          const meta = record.llm_metadata;
          const provName = meta ? (meta.provider === 'gemini' ? 'Gemini API' : meta.provider === 'openai' ? 'OpenAI API' : 'Local') : null;
          const modeName = meta ? (meta.mode === 'api' ? 'API' : meta.mode) : null;

          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                padding: '12px 16px',
                borderRadius: 'var(--radius-sm)',
                background: isFinal
                  ? 'rgba(168, 85, 247, 0.08)'
                  : isError
                  ? 'var(--danger-bg)'
                  : 'rgba(10, 13, 20, 0.6)',
                border: `1px solid ${
                  isFinal
                    ? 'rgba(168, 85, 247, 0.35)'
                    : isError
                    ? 'rgba(239, 68, 68, 0.4)'
                    : 'var(--border-subtle)'
                }`,
                fontSize: '13px',
              }}
            >
              {/* Header: Title + Badge + Duration */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    background: isFinal ? 'var(--primary-gradient)' : 'var(--bg-secondary)',
                    color: isFinal ? '#fff' : 'var(--text-muted)',
                    border: isFinal ? 'none' : '1px solid var(--border-subtle)',
                    textTransform: 'uppercase',
                  }}>
                    {isFinal ? 'FINAL ANSWER' : `Call ${record.call_number}/${maxCalls}`}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: '14px', color: isFinal ? '#c084fc' : 'var(--text-main)', fontFamily: 'monospace' }}>
                    {getDisplayName(record)}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--accent-cyan)', fontSize: '12px', fontFamily: 'monospace' }}>
                    {record.duration_ms} ms
                  </span>
                  {!isFinal && (
                    <span style={{ fontSize: '11px', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.05)', padding: '1px 6px', borderRadius: '3px' }}>
                      rem: {record.budget_remaining}
                    </span>
                  )}
                </div>
              </div>

              {/* Body: Structured Metadata fields */}
              {meta ? (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '3px',
                  background: 'rgba(0, 0, 0, 0.25)',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontFamily: 'monospace'
                }}>
                  <div>
                    <span style={{ color: 'var(--text-dim)' }}>Provider: </span>
                    <strong style={{ color: meta.provider === 'local' ? '#fbbf24' : '#34d399' }}>
                      {provName}
                    </strong>
                  </div>
                  {meta.model && (
                    <div>
                      <span style={{ color: 'var(--text-dim)' }}>Model: </span>
                      <span style={{ color: 'var(--text-muted)' }}>{meta.model}</span>
                    </div>
                  )}
                  <div>
                    <span style={{ color: 'var(--text-dim)' }}>Mode: </span>
                    <span style={{
                      color: meta.mode === 'api' ? '#34d399' : '#fbbf24',
                      fontWeight: 600,
                    }}>
                      {modeName}
                    </span>
                  </div>
                  {meta.reason && (
                    <div>
                      <span style={{ color: '#f87171' }}>Reason: </span>
                      <span style={{ color: '#fca5a5' }}>{meta.reason}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '3px',
                  background: 'rgba(0, 0, 0, 0.25)',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontFamily: 'monospace'
                }}>
                  <div>
                    <span style={{ color: 'var(--text-dim)' }}>Tool: </span>
                    <span style={{ color: 'var(--accent-cyan)' }}>{record.tool_name}</span>
                  </div>
                  {record.arguments?.keyword && (
                    <div>
                      <span style={{ color: 'var(--text-dim)' }}>Query: </span>
                      <span style={{ color: 'var(--text-main)' }}>{record.arguments.keyword}</span>
                    </div>
                  )}
                  {record.arguments?.page_number !== undefined && (
                    <div>
                      <span style={{ color: 'var(--text-dim)' }}>Page: </span>
                      <span style={{ color: 'var(--text-main)' }}>{record.arguments.page_number}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Result Summary */}
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                {record.result_summary}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
