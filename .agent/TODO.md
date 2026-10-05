# TODO

## P0
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

## P1
- [x] Add comprehensive test suite (direct factual, multi-page, contradiction/supersession, missing info, prompt injection, budget boundary)
- [x] Polish UI with sleek modern styling and real-time trace inspection
- [x] Entity x Attribute coverage matrix in AgentState & coverage-driven retrieval
- [x] Keyword component-term fallback for semantic planner entities
- [x] Grounded final answer synthesis without keyword hijacking or truncation

## P2
- [x] Written memo draft (architecture, justification, failure modes) in `MEMO.md`
- [x] Comprehensive documentation and live demo instructions in `README.md`

