# Architecture Decision Records (ADR)

## DEC-001: Unified 6-Call Budget Counter
- **Decision**: Pre-final LLM planning and all document tool executions consume from a single `CallBudget` instance with `MAX_CALLS = 6`.
- **Reason**: Problem statement strict constraint.
- **Status**: Accepted

## DEC-002: Deterministic Python Control Flow
- **Decision**: Use 1 planning LLM call to extract intent, entities, keywords, and likely headings. Use deterministic Python rules to orchestrate retrieval tool calls.
- **Reason**: Conserves budget for actual page retrieval while avoiding multi-turn LLM loops that deplete calls.
- **Status**: Accepted

## DEC-003: On-Demand Tool Access (No Caching)
- **Decision**: Document tools open PDF on-demand per page/heading search. No in-memory full text indexing or semantic caches.
- **Reason**: Comply with anti-caching / anti-RAG constraint.
- **Status**: Accepted
