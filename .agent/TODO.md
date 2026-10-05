# TODO

## P0: Core Engine & Constraints
- [x] Implement `CallBudget` with hard 6-call max and `BudgetExceededError`
- [x] Implement `CallLogger` with structured `CallRecord` and trace summary
- [x] Implement prescribed document tools (`list_documents`, `list_headings`, `search_keyword`, `get_page`) using `pypdf` without full caching
- [x] Implement `ToolWrapper` with pre-call budget consumption and error logging
- [x] Implement unit tests for budget (6 accepted, 7th raises `BudgetExceededError`)
- [x] Implement `AgentState` and `EvidenceStore`
- [x] Implement Planning LLM call (structured JSON output)
- [x] Implement deterministic adaptive retrieval controller
- [x] Implement Final Answer LLM call (enforces 1 call only, evidence-only, untrusted document context, "Insufficient information.")
- [x] Implement FastAPI backend endpoints (`/api/documents`, `/api/upload`, `/api/ask`, `/api/trace`)
- [x] Implement React/Vite web interface (document selector, PDF upload, question input, call counter [e.g. 4/6], answer & evidence display, call trace)

## P1: Retrieval, Coverage, and Grounding Precision
- [x] Add comprehensive test suite (direct factual, multi-page, contradiction/supersession, missing info, prompt injection, budget boundary)
- [x] Entity × Attribute coverage matrix in `AgentState` & coverage-driven candidate page ranking
- [x] Keyword component-term fallback for semantic planner entities (e.g. "intelligent agent" -> "intelligent", "agent")
- [x] Stopword filtering to avoid wasted keyword searches
- [x] Grounded final answer synthesis without keyword hijacking or comparative truncation
- [x] Intelligent agent definition gate (Page 4 formal percept-to-action definition prioritized over Page 1 history mentions)
- [x] Deterministic evidence relevance and unanswerability gate (returns "Insufficient information in the provided document" for unanswerable questions like "population of Japan")
- [x] Broad overview intent detection (`detect_broad_overview_question`) with heading navigation discovery and Step B keyword skip optimization

## P2: Observability, UI Transparency, and Agent Handover
- [x] Explicit LLM runtime observability (`LLMCallMetadata`) tracking API vs local rule-based fallback mode, latency, and sanitized error categories
- [x] Secret safety enforcement: zero leakage of API keys or auth headers in trace or client payloads
- [x] UI CallTrace card layout showing runtime badges (Gemini API vs Local Fallback, model, status, execution duration, sanitized error reasons)
- [x] Written memo draft (architecture, justification, failure modes) in `MEMO.md`
- [x] Comprehensive documentation and live demo instructions in `README.md`
- [x] Updated all `.agent/` project brain files (`ARCHITECTURE.md`, `CONSTRAINTS.md`, `CURRENT_STATE.md`, `DECISIONS.md`, `PROJECT_BRAIN.md`, `SESSION_LOG.md`, `TEST_STATUS.md`, `TODO.md`)
- [x] Created `HANDOVER.md` for seamless successor agent onboarding

## P3: Local Lexical Chunk Store & Candidate Discovery (Zero Vector DBs)
- [x] Implement deterministic sliding word-window chunker (`CHUNK_SIZE=550`, `CHUNK_OVERLAP=75`, page provenance, Unicode NFKD normalization)
- [x] Implement deterministic prompt injection detector in chunking metadata (`suspicious_instruction`)
- [x] Implement local JSON chunk store (`ChunkStore`) scoped by `doc_id` and SHA256 content hash with cross-document isolation and stale-index protection
- [x] Implement pure Python BM25 / TF-IDF lexical retriever with English root stemming, phrase matching, and entity × attribute co-occurrence bonuses
- [x] Integrate local chunk retrieval into `controller.py` candidate page discovery and `main.py` upload-time indexing
- [x] Add comprehensive 12-test retrieval suite in `test_retrieval.py` and verify full 34/34 test regression suite passing 100%


## Operational Runbook
- Ensure `.env` has valid `GEMINI_API_KEY` or `OPENAI_API_KEY` (system seamlessly falls back to local rule-based engine if keys are missing or 429 quota is hit).
- Backend server: `py -3.14 -m uvicorn backend.main:app --port 8000 --reload`
- Frontend dev (optional if editing components): `cd frontend && npm run dev`
- Frontend production build: `cd frontend && npm run build` (served automatically by FastAPI at `http://localhost:8000`)
