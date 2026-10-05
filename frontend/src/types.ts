export interface DocumentMetadata {
  doc_id: string;
  title: string;
  page_count: number;
  filename: string;
  size_bytes?: number;
  error?: string;
}

export interface EvidenceItem {
  source: string;
  page_number: number;
  content: string;
  relevance: string;
  relation: "SUPPORTS" | "SUPERSEDES" | "CONTRADICTS" | "CONTEXT" | string;
}

export interface CallRecord {
  call_number: number;
  call_type: string;
  tool_name: string;
  arguments: Record<string, any>;
  result_summary: string;
  timestamp: number;
  timestamp_iso?: string;
  duration_ms: number;
  success: boolean;
  error?: string;
  budget_remaining: number;
  llm_metadata?: {
    provider: string;
    model?: string | null;
    mode: string;
    reason?: string;
    error?: string;
  };
}

export interface AskResponse {
  question: string;
  document_id: string;
  status: string;
  final_answer: string;
  evidence: EvidenceItem[];
  calls_used: number;
  max_calls: number;
  budget_remaining: number;
  trace: CallRecord[];
  trace_summary: string;
  llm_calls?: Record<string, any>[];
  planner_llm_metadata?: Record<string, any>;
  final_llm_metadata?: Record<string, any>;
}
