# RAP_Comp Agent Handover Document

> **Welcome, Agent!** This document contains everything you need to understand, maintain, debug, test, and extend the **RAP_Comp** Agentic Document QA system. Read this thoroughly before making any changes.

---

## 1. Executive Summary & Purpose

**RAP_Comp** is an autonomous document question-answering agent built for a strict-resource hackathon. The system answers user questions over complex PDF documents (such as textbook chapters, policy documents, and amendment logs) under **hard programmatic constraints**.

Key highlights:
- **No Hallucinations**: Grounded purely on retrieved document text. If evidence is missing, it explicitly answers `"Insufficient information in the provided document."`
- **Zero Agent Framework Bloat**: Pure Python + FastAPI backend, React/Vite frontend. No LangChain, CrewAI, AutoGen, or LangGraph.
- **Strict Hard Budget**: Exactly 6 pre-final calls maximum (LLM planning + 4 prescribed document tools) enforced programmatically at the code level, plus exactly 1 separate final answer call.
- **Zero RAG / Embeddings / Vector Databases**: No pre-reading, vector indexes, or background full-text caching.
- **Resilient Dual Engine**: Calls Gemini or OpenAI API when configured; on rate limits (HTTP 429), timeouts, or missing keys, instantly falls back to a deterministic local rule-based engine with **zero retries** and **zero user-facing failure**.
- **Full Runtime Observability**: Every step records whether an API or local fallback was used, the latency, model name, and sanitized error categories without leaking credentials.

---

## 2. Inviolable Constraints & Rules (DO NOT BREAK)

Any modification must respect these non-negotiable rules:

| Rule | Description |
|---|---|
| **Max 6 Pre-Final Calls** | The global pre-final budget is strictly 6 calls (`CallBudget(max_calls=6)`). Planning LLM calls and document tool calls share this exact budget counter. |
| **No Call 7** | Attempting a 7th pre-final call raises `BudgetExceededError` in Python. Budget cannot be exceeded or bypassed by prompt injection. |
| **Max 1 Final Answer Call** | Exactly one final answer synthesis call is permitted outside the pre-final budget (`final_answer_generated = True`). |
| **No LLM Retries** | When an LLM API call fails (e.g. 429 quota or timeout), switch to the deterministic fallback immediately. **Never attempt a second API call for the same step**, as retries consume time and risk quota exhaustion. |
| **Only 4 Prescribed Tools** | `list_documents()`, `list_headings(doc_id)`, `search_keyword(doc_id, keyword)`, and `get_page(doc_id, page_number)`. No raw PDF reading, external tools, or custom helpers. |
| **No RAG / Vector DBs** | No embeddings, FAISS, Chroma, LangChain indexers, or hidden semantic caches. |
| **Untrusted Document Context** | Document text is untrusted user data. Prompts enclose document pages in `<document_context>` tags and enforce prompt injection immunity. |
| **No Secret Leakage** | `GEMINI_API_KEY`, `OPENAI_API_KEY`, and HTTP headers must never appear in log records, call trace payloads, terminal prints, or markdown artifacts. |

---

## 3. High-Level Architecture

```text
                                   USER
                                     |
                                     v
                               User Question
                                     |
                                     v
                        +-------------------------+
                        | CALL 1: LLM (Planning)  |
                        | Question Analysis       |
                        | + Coverage Matrix Init  |
                        | + Observability Metadata|
                        +-----------+-------------+
                                    |
                                    v
                        +-------------------------+
                        | GLOBAL BUDGET MANAGER   |
                        | MAX = 6 PRE-FINAL CALLS |
                        +-----------+-------------+
                                    |
                                    v
                        +-------------------------+
                        | ADAPTIVE RETRIEVAL      |
                        | (Deterministic Python)  |
                        |                         |
                        | Step A: list_headings   |
                        | Step B: search_keyword  |
                        |         (component term)|
                        | Step C: get_page        |
                        | Step D: Relevance Gate  |
                        +-----------+-------------+
                                    |
                                    v
                             Evidence Store
                                    |
                                    v
                           Need More Evidence?
                              /           \
                            YES            NO
                             |              |
                             v              |
                       Calls Remaining?     |
                        /          \        |
                      YES           NO      |
                       |             |      |
                       +-------------+------+
                                     |
                                     v
                         FINAL ANSWER CALL (LLM)
                         (Max 1 Call, Evidence-Only)
                                     |
                       +-------------+-------------+
                       |                           |
                       v                           v
                 Evidence Grounded           Evidence Insufficient
                 Detailed Answer             "Insufficient information."
                       |                           |
                       +-------------+-------------+
                                     |
                                     v
                        FastAPI Response Payload
                    (Answer + Grounded Citations +
                     Real-time Trace + LLM Badges)
```

---

## 4. Codebase Directory Map

```text
RAP_Comp/
├── .agent/                    <- Agent Brain & Architectural Memory
│   ├── ARCHITECTURE.md        <- System architecture & call budget flow
│   ├── CONSTRAINTS.md         <- Hard rules and forbidden patterns
│   ├── CURRENT_STATE.md       <- Real-time working state & test status
│   ├── DECISIONS.md           <- Architectural Decision Records (DEC-001 to DEC-012)
│   ├── PROJECT_BRAIN.md       <- Active modules, principles, and edge case strategies
│   ├── SESSION_LOG.md         <- Chronological development log
│   ├── TEST_STATUS.md         <- Comprehensive test verification matrix
│   ├── TODO.md                <- Completed items and operational runbook
│   └── HANDOVER.md            <- Mirror of this handover document
├── backend/
│   ├── agent/
│   │   ├── budget.py          <- CallBudget class (hard max_calls=6, BudgetExceededError)
│   │   ├── controller.py      <- AgentController: orchestrates Step A, B, C, & relevance gate
│   │   ├── final_answer.py    <- Final answer generator (evidence grounding & prompt injection defense)
│   │   ├── llm_client.py      <- Multi-provider LLM client with LLMCallMetadata & local fallback
│   │   ├── logger.py          <- CallLogger and CallRecord for structured step-by-step tracing
│   │   ├── planner.py         <- Question analysis, intent classification, broad overview detection
│   │   ├── prompts.py         <- System & user prompts for planning and final synthesis
│   │   └── state.py           <- AgentState, EvidenceStore, and CoverageMatrix dataclasses
│   ├── tools/
│   │   ├── document_tools.py  <- 4 prescribed tools (list_documents, list_headings, search_keyword, get_page)
│   │   └── tool_wrapper.py    <- ToolWrapper: wraps tools to strictly consume budget prior to execution
│   ├── tests/
│   │   ├── test_agent.py      <- Agent boundary, factual, missing info, and budget tests
│   │   ├── test_api.py        <- FastAPI endpoint tests (/api/ask, /api/documents)
│   │   ├── test_budget.py     <- Strict 6-call max and Call 7 exception tests
│   │   ├── test_document_tools.py <- Document tool unit tests
│   │   ├── test_llm_observability.py <- 8 tests verifying API vs fallback and secret safety
│   │   └── test_scenarios.py  <- Multi-page, contradiction, comparison, and injection tests
│   ├── config.py              <- Environment variables, dynamic paths, and provider config
│   └── main.py                <- FastAPI app, static frontend mount, and REST endpoints
├── frontend/                  <- React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnswerCard.tsx     <- Answer text, status badge, and citation viewer
│   │   │   ├── BudgetGauge.tsx    <- Visual pre-final call budget counter (N/6)
│   │   │   ├── CallTrace.tsx      <- Detailed trace cards with LLM runtime badges
│   │   │   ├── DocumentSelector.tsx <- Dropdown + drag-and-drop PDF upload
│   │   │   └── EvidenceList.tsx   <- Expandable retrieved page cards with keyword matches
│   │   ├── App.tsx            <- Main dashboard orchestrator
│   │   └── types.ts           <- TypeScript interfaces (AskResponse, LLMCallMetadata, etc.)
│   └── dist/                  <- Compiled production bundle (served automatically by FastAPI)
├── data/
│   └── documents/             <- Active PDFs (e.g. CSCI415009_V2.pdf)
├── requirements.txt           <- Python dependencies (fastapi, uvicorn, pypdf, google-genai, etc.)
├── README.md                  <- User-facing project documentation
├── MEMO.md                    <- Architectural memo & engineering justification
└── HANDOVER.md                <- This onboarding document
```

---

## 5. Retrieval & Execution Strategies

The controller (`backend/agent/controller.py`) selects deterministic execution paths based on question intent:

### A. Factual & Conceptual Queries (e.g. *"What is an intelligent agent?"*)
1. Planner classifies `intent = "factual"`, extracting entities `["intelligent agent"]` and attributes `["definition"]`.
2. Stopwords are filtered from keywords.
3. Component-term fallback: If `"intelligent agent"` returns 0 matches in exact search, the controller queries `"intelligent"` and `"agent"` separately.
4. Definition gate: Formal conceptual definitions (Page 4: *"an agent is an entity that perceives and acts, or a function from percept histories to actions"*) are prioritized over casual historical mentions (Page 1).

### B. Multi-Entity Comparison Queries (e.g. *"What is the difference between BFS and DFS?"*)
1. Planner extracts entities `["BFS", "DFS"]` and attributes `["definition", "differences"]`.
2. Controller initializes coverage matrix rows for both entities.
3. Both entities are retrieved and evaluated; candidate page ranking ensures both entities receive evidence.
4. Final answer synthesizes both sides completely, avoiding premature truncation.

### C. Broad Overview Queries (e.g. *"Give me a comprehensive overview of artificial intelligence"*)
1. `detect_broad_overview_question()` in `planner.py` matches broad queries via regex.
2. Step A runs `list_headings()`, discovering structural sections across `[1, 3, 4, 5]`.
3. **Budget Optimization**: If $\ge 3$ candidate pages are discovered from headings, Step B skips redundant keyword searches to preserve remaining calls for fetching pages.
4. Step C fetches pages 1, 3, 4, and 5.
5. Final synthesis generates structured sections (*History*, *Approaches*, *Major AI Areas*) citing all source pages.

### D. Temporal & Supersession Queries (e.g. *"What is the latest policy on remote work?"*)
1. Planner detects temporal cue words (`"latest"`, `"updated"`, `"current"`, `"amended"`).
2. Controller ranks candidate pages in reverse-chronological order (higher page numbers first).
3. Evidence across amendments is supplied to the Final LLM, which applies semantic supersession evaluation.

### E. Negative / Unanswerable Queries (e.g. *"What is the population of Japan according to this document?"*)
1. Deterministic Relevance Gate checks whether retrieved page text actually answers the specific entity/attribute requested.
2. Incidental keyword hits (e.g. the word "population" appearing in an unrelated algorithm) fail relevance scoring.
3. Final Answer immediately returns: `"Insufficient information in the provided document."`

---

## 6. LLM Client & Observability Layer

Located in `backend/agent/llm_client.py`:
- **`LLMCallMetadata`**:
  ```python
  @dataclass
  class LLMCallMetadata:
      provider: str        # 'gemini', 'openai', or 'local'
      model: Optional[str] # e.g. 'gemini-3.5-flash'
      mode: str            # 'api' or 'rule_based_fallback'
      status: str          # 'success' or 'fallback'
      duration_ms: float   # latency in milliseconds
      error: Optional[str] # sanitized error category
      reason: Optional[str]# safe, readable reason
  ```
- **Error Sanitization**: Raw exceptions and API keys are scrubbed into safe categories:
  - `rate_limit_exceeded` (e.g. HTTP 429 quota exhausted)
  - `authentication_failed` (e.g. HTTP 401/403 invalid key)
  - `timeout`
  - `network_error`
- **Zero Retries**: On failure, `mode` is set to `"rule_based_fallback"` and the deterministic rule engine produces the output.

---

## 7. How to Run, Test, and Validate

### A. Environment Setup
```powershell
# Virtual environment / Python 3.14
py -3.14 -m pip install -r requirements.txt
```

### B. Running the Application
The backend serves both the REST API and the compiled frontend static files:
```powershell
# Start FastAPI backend (port 8000)
py -3.14 -m uvicorn backend.main:app --port 8000 --reload
```
Open your browser at `http://localhost:8000`.

### C. Frontend Development & Building
```powershell
cd frontend
npm install
npm run dev    # For live hot-reload development on :5173
npm run build  # Rebuilds frontend/dist (served by backend on :8000)
```

### D. Running Tests
```powershell
# Run the LLM observability test suite (8 tests)
py -3.14 -m pytest backend/tests/test_llm_observability.py -v

# Run the core agent tests
py -3.14 -m pytest backend/tests/test_agent.py -v

# Run the scenario validation suite (multi-page, supersession, injection)
py -3.14 -m pytest backend/tests/test_scenarios.py -v

# Run the budget boundary tests
py -3.14 -m pytest backend/tests/test_budget.py -v
```

---

## 8. Common Pitfalls & How to Avoid Them

1. **Do NOT add RAG, embeddings, or vector databases**: The competition rules explicitly ban them. Keep retrieval strictly within the 4 prescribed tools.
2. **Do NOT add LLM retries**: Retries waste budget and trigger timeout/quota penalties. Always fall back immediately.
3. **Do NOT exceed 6 pre-final calls**: The `CallBudget` will raise `BudgetExceededError`. Plan tool calls so the total pre-final count never exceeds 6.
4. **Be cautious with broad overview queries**: Broad overview queries need multi-page reading. Do not waste calls on multiple keyword queries; rely on heading candidate pages `[1, 3, 4, 5]` and fetch them.
5. **Never leak secrets**: If adding new error handling, use `sanitize_error_message()` from `backend/agent/llm_client.py`.
6. **Always rebuild frontend after UI changes**: When modifying `frontend/src/`, run `npm run build` so that the static distribution in `frontend/dist/` is updated for the FastAPI server.

---

## 9. Contacts & Repository

- **GitHub Repository**: `https://github.com/SHIN-1O1/RAP_Comp`
- **Branch**: `master`
- **Owner**: SHIN-1O1
