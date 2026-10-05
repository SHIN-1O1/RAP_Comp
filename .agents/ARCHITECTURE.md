# System Architecture

## Architecture Overview
The system implements a strictly budgeted, code-governed document question-answering agent without RAG, embeddings, or vector databases.

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
                        | * Heading Discovery     |
                        |   (list_headings)       |
                        | * Keyword Search        |
                        |   (search_keyword)      |
                        | * Candidate Page Rank   |
                        | * Page Fetch (get_page) |
                        | * Relevance Gate        |
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
                        API Response + Call Trace
                    (With LLM Runtime Observability)
```

---

## Core Components

### 1. Global Call Budget Manager (`backend/agent/budget.py`)
- **Capacity**: Strict maximum of 6 pre-final calls (`CallBudget(max_calls=6)`).
- **Shared Budget**: Pre-final LLM planning calls and document tool executions share the same counter.
- **Hard Enforcement**: Attempting a 7th pre-final call immediately raises `BudgetExceededError` in Python. Budget cannot be exceeded by prompt manipulation.
- **Final Answer Isolation**: Exactly one final answer synthesis call is permitted outside the pre-final budget.

### 2. Prescribed Document Tools (`backend/tools/document_tools.py`)
Only 4 prescribed tools are allowed to access documents (wrapped via `backend/tools/tool_wrapper.py`):
- `list_documents() -> List[str]`: Enumerate available PDF files in `data/documents/`.
- `list_headings(doc_id: str) -> List[Dict[str, Any]]`: Extract document outline / bookmark titles with page numbers.
- `search_keyword(doc_id: str, keyword: str) -> List[int]`: Case-insensitive exact substring search returning page numbers where the term occurs.
- `get_page(doc_id: str, page_number: int) -> str`: Retrieve the raw text of a specific 1-indexed page.

**Forbidden**: No RAG, no embeddings, no vector databases, no full-document caching or pre-reading, and no external agent frameworks (LangChain, CrewAI, AutoGen).

### 3. Planning & Coverage Matrix (`backend/agent/planner.py`)
- Executes Call #1 (LLM or deterministic fallback).
- Classifies question intent: `factual`, `comparison`, `temporal`, `unanswerable`, or `broad_overview`.
- Extracts semantic `entities` and target `attributes`.
- Initializes an Entity × Attribute Coverage Matrix in `AgentState`:
  - `SUPPORTED`: Attribute established by retrieved evidence.
  - `CONTRADICTED`: Conflicting evidence found.
  - `SUPERSEDES`: Superseded by newer amendment/policy.
  - `NOT_ESTABLISHED`: Unresolved claim requiring further retrieval.
- Computes prioritized search terms with stopword filtering and component-term fallback.

### 4. Deterministic Adaptive Retrieval Controller (`backend/agent/controller.py`)
- Orchestrates tool calls based on intent, remaining budget, and coverage state:
  1. **Heading Navigation (Step A)**: Queries `list_headings()` when outline data provides direct section cues (especially for comparisons, structured topics, and broad overviews).
  2. **Keyword Retrieval (Step B)**:
     - Queries `search_keyword()` for unresolved terms.
     - Automatically falls back from multi-word phrases (e.g. `"intelligent agent"`) to component terms (`"intelligent"`, `"agent"`).
     - **Broad-Overview Optimization**: If Step A already discovered $\ge 3$ candidate pages from headings, Step B skips redundant keyword searches to preserve call budget for fetching pages.
  3. **Candidate Page Scoring & Fetching (Step C)**:
     - Computes candidate page scores based on unresolved claim relevance, keyword density, and reverse-chronological order for temporal queries (`"latest"`, `"updated"`).
     - Fetches top-ranked pages via `get_page()`.
  4. **Evidence Relevance & Answerability Gate**:
     - Evaluates whether retrieved evidence actually answers the specific question.
     - Rejects incidental keyword matches (e.g. questions asking for "population of Japan" or unrelated algorithms).
     - Prioritizes conceptual definitions (e.g. Page 4 percept-to-action agent definition over Page 1 historical mentions).

### 5. Final Answer Generator (`backend/agent/final_answer.py`)
- Executes exactly 1 final answer call.
- Strictly conditioned on retrieved evidence from `EvidenceStore`.
- Strict prompt injection defense: instructions inside PDF texts are treated as untrusted data and cannot override system instructions.
- Returns `"Insufficient information in the provided document."` when evidence is missing or fails the relevance gate.
- Appends clean source citations (`Source: Page X`).

### 6. LLM Runtime Observability (`backend/agent/llm_client.py`)
- Every LLM invocation records a structured `LLMCallMetadata` object:
  - `provider`: `"gemini"`, `"openai"`, or `"fallback"`
  - `model`: Model name (e.g. `gemini-3.5-flash`)
  - `mode`: `"api"` (real network call) vs `"rule_based_fallback"` (local deterministic engine)
  - `status`: `"success"` or `"fallback"`
  - `duration_ms`: Execution latency in milliseconds
  - `error`: Sanitized error category (`"rate_limit_exceeded"`, `"authentication_failed"`, `"timeout"`, `"network_error"`, or `"unknown"`)
  - `reason`: Safe, user-friendly explanation (e.g. `"quota / rate limit exceeded (429)"`)
- **Zero Secret Leakage**: API keys, auth headers, and raw credentials are never recorded in metadata, call records, logs, or UI responses.
- Propagated to `AgentState`, `CallLogger`, and `/api/ask` response payload.

### 7. User Interface (`frontend/src/`)
- Built with React, TypeScript, and Vite.
- Real-time `BudgetGauge` tracking pre-final calls (`N / 6`).
- `DocumentSelector` with drag-and-drop PDF upload.
- `AnswerCard` displaying answer text, status badge, and grounded source citations.
- `EvidenceList` with expandable page evidence cards.
- `CallTrace` detailing step-by-step executions, arguments, durations, and prominent LLM badges indicating API vs Fallback execution.
