# Architecture Decision Records (ADR)

## DEC-001: Unified 6-Call Budget Counter
- **Decision**: Pre-final LLM planning and all document tool executions consume from a single `CallBudget` instance with `MAX_CALLS = 6`.
- **Reason**: Strict compliance with problem statement constraints.
- **Status**: Accepted & Implemented

## DEC-002: Deterministic Python Control Flow & Temporal Ordering
- **Decision**: Use 1 planning LLM call to extract intent, entities, attributes matrix, keywords, and headings. Use deterministic Python rules to orchestrate retrieval tool calls and prioritize reverse page ordering when temporal/supersession keywords ("current", "latest", "updated", "revised") are detected.
- **Reason**: Conserves budget for actual page retrieval while ensuring newer amendments/superseding policies are read.
- **Status**: Accepted & Implemented

## DEC-003: On-Demand Tool Access (No Caching)
- **Decision**: Document tools open PDF on-demand per page/heading search. No in-memory full text indexing or semantic caches.
- **Reason**: Comply with anti-caching / anti-RAG constraint.
- **Status**: Accepted & Implemented

## DEC-004: Comprehensive Prompt System & Coverage Matrix
- **Decision**: Adopt explicit entity-attribute matrix parsing, prompt injection defense, outside-knowledge prohibition, and standard `ANSWER / EVIDENCE / STATUS` final formatting.
- **Reason**: Eliminates hallucinations and guarantees exact evidence tracing.
- **Status**: Accepted & Implemented

## DEC-005: Rate Limit Resilience & Graceful Fallback
- **Decision**: Wrap LLM calls with a multi-model fallback chain (`gemini-3.5-flash` → `gemini-3.8-flash`) and fall back to the deterministic rule-based engine if 429 quota or network errors occur.
- **Reason**: Ensures 0% runtime crash risk during live evaluations under free-tier API quotas.
- **Status**: Accepted & Implemented
