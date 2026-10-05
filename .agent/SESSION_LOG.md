# Session Log

## 2026-10-05 10:45

### Completed
- Inspected repository and environment (`CSCI415009_V2.pdf`, Python 3.14, Node 24, npm 11).
- Initialized `.agent/` project brain files (`PROJECT_BRAIN.md`, `CONSTRAINTS.md`, `CURRENT_STATE.md`, `TODO.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `SESSION_LOG.md`, `TEST_STATUS.md`).

### Decisions
- DEC-001, DEC-002, DEC-003 adopted.

### Tests
- Environment check passed.

## 2026-10-05 10:49

### Completed
- Phase 1 Foundation:
  - `backend/config.py`: dynamic paths and configuration.
  - `backend/agent/budget.py`: strict `CallBudget` (max 6 pre-final calls, `BudgetExceededError`).
  - `backend/agent/logger.py`: `CallLogger` and `CallRecord`.
  - `backend/tools/document_tools.py`: 4 prescribed tools (`list_documents`, `list_headings`, `search_keyword`, `get_page`).
  - `backend/tools/tool_wrapper.py`: strict allowlist and pre-execution budget consumption.
  - `backend/tests/test_budget.py` and `backend/tests/test_document_tools.py`.

### Tests
- 8/8 unit tests passed.

## 2026-10-05 10:56

### Completed
- Phase 2 & 3: Agent Architecture & Verification:
  - `backend/agent/state.py`: compact `AgentState` and `EvidenceItem`.
  - `backend/agent/prompts.py`: structured planning schema and strict verification prompt.
  - `backend/agent/llm_client.py`: multi-provider (Gemini, OpenAI, deterministic fallback) with disabled hidden retries.
  - `backend/agent/planner.py`: Call 1 planning step.
  - `backend/agent/final_answer.py`: 1 separate final answer call with untrusted text defense and "Insufficient information." rules.
  - `backend/agent/controller.py`: adaptive deterministic retrieval controller.
- Phase 4: Full Stack Integration:
  - `backend/main.py`: FastAPI backend with PDF upload, document listing, and `/api/ask` endpoints.
  - `frontend/`: React + TypeScript + Vite SPA with `BudgetGauge`, `DocumentSelector`, `AnswerCard`, `EvidenceList`, and `CallTrace`. Built to `frontend/dist`.
- Phase 5 & 6: Evaluation & Documentation:
  - 17/17 automated tests passing covering budget boundaries, missing information, supersession, and prompt injection defense.
  - Generated `MEMO.md` covering architecture, justifications, and failure modes.
  - Generated `README.md` with complete architecture and demonstration instructions.
