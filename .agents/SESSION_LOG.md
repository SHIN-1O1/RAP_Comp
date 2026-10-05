# Session Log

## 2026-10-05 10:45

### Completed
- Inspected repository and environment (`CSCI415009_V2.pdf`, Python 3.14, Node 24, npm 11).
- Initialized `.agent/` project brain files (`PROJECT_BRAIN.md`, `CONSTRAINTS.md`, `CURRENT_STATE.md`, `TODO.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `SESSION_LOG.md`, `TEST_STATUS.md`).

### Decisions
- DEC-001, DEC-002, DEC-003 adopted.

### Tests
- Environment check passed.

---

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

---

## 2026-10-05 11:24

### Completed
- Phase 2 to Phase 6 Full Implementation:
  - `backend/agent/state.py`, `planner.py`, `controller.py`, `final_answer.py`, `llm_client.py`.
  - Full React SPA Frontend with BudgetGauge, DocumentSelector, AnswerCard, EvidenceList, CallTrace.
  - 17/17 automated test matrix passing.
  - Written Memo (`MEMO.md`) & `README.md`.
  - Created & pushed public GitHub repository: `https://github.com/SHIN-1O1/RAP_Comp`.

---

## 2026-10-05 11:38
 
### Completed
- Integrated comprehensive prompt specification (Coverage Matrix, Entity-Attribute breakdown, Prompt Injection Defense, standard `ANSWER/EVIDENCE/STATUS` formatting).
- Updated all `.agent/` project brain files (`PROJECT_BRAIN.md`, `CONSTRAINTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `SESSION_LOG.md`, `TEST_STATUS.md`, `TODO.md`).
- Verified git status & repository synchronization.

---

## 2026-10-05 12:45

### Completed
- Refined retrieval and planner coverage architecture:
  - Removed multi-model LLM retries (DEC-005).
  - Eliminated `keywords[:2]` limit in controller.
  - Implemented full Entity × Attribute coverage matrix in `AgentState` (DEC-006).
  - Implemented coverage-driven candidate page selection.
  - Delegated contradiction/supersession resolution strictly to the Final Answer LLM (DEC-007).
  - Fixed planner fallback state population.
- Added component-term fallback for multi-word planner entities (DEC-008).

---

## 2026-10-05 13:05

### Completed
- Fixed Final Answer Synthesis & Grounding Behavior (DEC-009):
  - Updated `FINAL_ANSWER_SYSTEM_PROMPT` and `FINAL_ANSWER_USER_PROMPT` to prioritize question answering over incidental keyword matches.
  - Refined rule-based fallback in `llm_client.py` with question relevance scoring and target-entity checking.
  - Resolved comparative truncation for BFS vs DFS and multi-entity comparison queries.
  - Eliminated keyword hijacking (e.g. rejecting Robinson's 1965 algorithm when asked about A*).
  - Formatted source citations as clean secondary metadata (`Source: Page X`).
  - Verified targeted 5-question validation suite and `backend/tests/test_scenarios.py`.
  - Pushed to GitHub repository: `https://github.com/SHIN-1O1/RAP_Comp`.

---

## 2026-10-05 13:30

### Completed
- Definition Precision & Stopword Filtering:
  - Filtered common English stopwords from keyword search queries to prevent wasted budget calls.
  - Refined intelligent agent definition selection: prioritizes Page 4 formal definition (perceives and acts / function from percept histories to actions) over Page 1 historical mentions.

---

## 2026-10-05 13:55

### Completed
- Evidence-to-Question Relevance & Answerability Gate (DEC-011):
  - Added strict answerability verification in `controller.py` and `final_answer.py`.
  - Tested negative cases: questions about facts completely outside document scope (e.g. "What is the population of Japan according to this document?") reliably return `"Insufficient information in the provided document."` without hallucinated text.

---

## 2026-10-05 14:10

### Completed
- Broad Overview Intent & Heading Optimization (DEC-010):
  - Added `detect_broad_overview_question()` in `planner.py` supporting regex queries such as `"Explain everything about artificial intelligence"` and `"Give me a comprehensive overview of artificial intelligence"`.
  - Configured heading navigation to discover representative section pages `[1, 3, 4, 5]`.
  - Step B skips redundant keyword searches when $\ge 3$ heading candidate pages exist, saving the 6-call budget for reading pages.
  - Final answer synthesizes structured sections (`History`, `Approaches`, `Major AI Areas`) citing all retrieved pages.

---

## 2026-10-05 14:20

### Completed
- Explicit LLM Runtime Observability & UI Transparency (DEC-012):
  - Implemented `LLMCallMetadata` dataclass tracking `provider`, `model`, `mode` (`"api"` vs `"rule_based_fallback"`), `status`, `duration_ms`, `error`, and `reason`.
  - Implemented error sanitization stripping sensitive credentials while categorizing errors into 429 quota, 401/403 auth, timeout, or network issues.
  - Updated `AgentState`, `CallLogger`, and `/api/ask` response payload.
  - Updated React `CallTrace.tsx` to display distinct badges for Gemini API vs Local Rule-Based Fallback with model, latency, and failure reasons.
  - Rebuilt frontend static assets (`npm run build`).
  - Created `backend/tests/test_llm_observability.py` with 8 passing test cases.

---

## 2026-10-05 14:35

### Completed
- Agent Handover & Documentation Alignment:
  - Updated all 8 files in `.agent/` (`ARCHITECTURE.md`, `CONSTRAINTS.md`, `CURRENT_STATE.md`, `DECISIONS.md`, `PROJECT_BRAIN.md`, `SESSION_LOG.md`, `TEST_STATUS.md`, `TODO.md`).
  - Created comprehensive onboarding document `HANDOVER.md` in root directory and `.agent/HANDOVER.md`.
