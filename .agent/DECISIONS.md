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

## DEC-005: Strict Budget Compliance & Local Rule Fallback (No Multi-Model Retries)
- **Decision**: Remove multi-model LLM retry chains. Exactly 1 API attempt per LLM call; on rate limits (429) or failures, immediately fall back to the deterministic local rule-based engine without secondary API calls.
- **Reason**: Guarantees zero hidden LLM calls and strict budget compliance.
- **Status**: Accepted & Implemented

## DEC-006: Entity x Attribute Coverage Matrix & Coverage-Driven Retrieval
- **Decision**: Model questions as an Entity x Attribute grid in `AgentState`. Candidate pages are scored and ranked deterministically by density of un-retrieved entity-attribute combinations.
- **Reason**: Prevents premature stopping and ensures all entities and comparison dimensions are retrieved.
- **Status**: Accepted & Implemented

## DEC-007: LLM-Driven Contradiction & Supersession Resolution
- **Decision**: Avoid heuristic assignment of `SUPERSEDES` in Python controller. All retrieved page evidence across revisions is passed directly to the Final LLM for reasoned supersession evaluation.
- **Reason**: Eliminates fragile keyword heuristics and allows semantic resolution of policy amendments.
- **Status**: Accepted & Implemented

## DEC-008: Keyword Component Term Fallback
- **Decision**: When multi-word semantic planner entities (e.g. `"intelligent agent"`) yield 0 matches in exact keyword search, automatically fall back to querying unsearched individual component terms (`"intelligent"`, `"agent"`).
- **Reason**: Retains rich semantic entities in `AgentState` while ensuring exact string matching in PDFs succeeds.
- **Status**: Accepted & Implemented

## DEC-009: Question-Relevance-Driven Final Answer Synthesis
- **Decision**: Final answer generator must explicitly prioritize question answering over incidental keyword matches (e.g. rejecting Robinson's algorithm when asked about A*). Multi-part and comparative queries (e.g. BFS vs DFS) must explain all entities and contrast differences completely rather than truncating at the first matching sentence fragment. Source citations format cleanly as secondary metadata (`Source: Page X`).
- **Reason**: Prevents answer truncation, eliminates keyword hijacking, and guarantees complete grounded responses.
- **Status**: Accepted & Implemented

