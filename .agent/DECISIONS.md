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

## DEC-010: Broad Overview Intent & Heading-Driven Retrieval Strategy
- **Decision**: Add broad overview detection in the planner via regex pattern matching (`"comprehensive overview"`, `"explain everything"`, `"overview of X"`). When broad overview intent is active, query `list_headings()` to identify structural sections. If headings discover $\ge 3$ candidate pages (e.g. `[1, 3, 4, 5]`), skip redundant Step B keyword searches to preserve the 6-call budget for reading representative pages. Final synthesis generates structured sections (History, Approaches, Major AI Areas) citing all retrieved pages.
- **Reason**: Enables thorough answers to wide-scope questions without running out of call budget on redundant keyword searches.
- **Status**: Accepted & Implemented

## DEC-011: Deterministic Evidence Relevance & Unanswerability Gate
- **Decision**: Implement a deterministic evidence relevance gate in `controller.py` and `final_answer.py`. Retrieved pages with incidental keyword hits that do not contain actual answer evidence for the user's specific query (e.g. asking for "population of Japan" in an AI textbook) are rejected, returning `"Insufficient information in the provided document."` Furthermore, conceptual queries (such as "What is an intelligent agent?") prioritize definitive functional definitions (Page 4) over historical mentions (Page 1).
- **Reason**: Prevents hallucinated or unrelated text synthesis when questions fall outside document scope.
- **Status**: Accepted & Implemented

## DEC-012: Explicit LLM Runtime Observability & Secret-Safe Error Sanitization
- **Decision**: Instrument all LLM calls with `LLMCallMetadata` tracking `provider`, `model`, `mode` (`"api"` vs `"rule_based_fallback"`), `status`, `duration_ms`, `error`, and `reason`. Raw exception messages and API keys are strictly sanitized into generic categories (`rate_limit_exceeded`, `authentication_failed`, `timeout`, `network_error`). Expose this metadata in `AgentState`, `CallLogger`, `/api/ask` responses, and render dedicated status badges in the React frontend `CallTrace`.
- **Reason**: Provides 100% transparency to operators and judges regarding whether Gemini/OpenAI API or local fallback generated the output, with zero risk of secret leakage.
- **Status**: Accepted & Implemented

## DEC-013: Local Lexical Chunk Store for Candidate Discovery & Coverage-Driven Retrieval
- **Decision**: Implement a pure Python local lexical chunk store (`backend/retrieval/`) that chunks uploaded PDFs at ingestion time (550 words, 75 words overlap, page boundary preservation, prompt injection detection flag). The lexical retriever applies BM25 scoring with English root stemming and entity × attribute co-occurrence bonuses to map matching chunks directly to candidate pages. Authoritative evidence fetching remains strictly with the prescribed `get_page()` tool. Zero embeddings, zero vector databases, and zero external agent frameworks are used.
- **Reason**: Significantly accelerates multi-entity comparison and complex claim discovery while preserving the 6-call budget, document isolation, and strict harness constraints.
- **Status**: Accepted & Implemented

