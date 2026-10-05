# System Architecture

## Architecture Overview
The system implements a strictly budgeted, code-governed document question-answering agent with a **Local Lexical Chunk Store** for candidate page discovery without embeddings, vector databases, or external RAG frameworks.

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
                        | LOCAL LEXICAL RETRIEVAL |
                        | (Zero LLM / Zero Vectors|
                        | BM25 + Stemmed Matching |
                        | Chunk -> Candidate Pages|
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
                        | * Coverage Page Rank    |
                        | * Authoritative Fetch   |
                        |   (get_page)            |
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

### 1. Local Chunk Store & Lexical Retriever (`backend/retrieval/`)
- **Deterministic Chunking (`chunker.py`)**: Slices uploaded PDF pages into ~550-word chunks with 75-word overlap, preserving exact page provenance and section metadata without splitting across page boundaries.
- **Prompt Injection Filter**: Flags suspicious instructions (`"suspicious_instruction": True`) without deleting factual content.
- **Local Chunk Store (`chunk_store.py`)**: Scoped strictly by `doc_id` and SHA256 file content hash in local JSON files. Guarantees complete document isolation and stale-index protection.
- **BM25 Lexical Retriever (`lexical_retriever.py`)**: Pure Python BM25 / TF-IDF scoring with English root stemming, multi-word exact phrase matching, and entity × attribute co-occurrence bonuses. Maps matching chunks directly to ranked candidate pages.
- **Zero Embedding / Zero Vector DB Guarantee**: Uses standard Python dictionaries and mathematics; no FAISS, Chroma, Pinecone, or LangChain.

### 2. Global Call Budget Manager (`backend/agent/budget.py`)
- **Capacity**: Strict maximum of 6 pre-final calls (`CallBudget(max_calls=6)`).
- **Shared Budget**: Pre-final LLM planning calls and document tool executions share the same counter.
- **Hard Enforcement**: Attempting a 7th pre-final call immediately raises `BudgetExceededError` in Python. Budget cannot be exceeded by prompt manipulation.
- **Final Answer Isolation**: Exactly one final answer synthesis call is permitted outside the pre-final budget.

### 3. Prescribed Document Tools (`backend/tools/document_tools.py`)
Only 4 prescribed tools are allowed to access documents (wrapped via `backend/tools/tool_wrapper.py`):
- `list_documents() -> List[str]`: Enumerate available PDF files in `data/documents/`.
- `list_headings(doc_id: str) -> List[Dict[str, Any]]`: Extract document outline / bookmark titles with page numbers.
- `search_keyword(doc_id: str, keyword: str) -> List[int]`: Case-insensitive exact substring search returning page numbers where the term occurs.
- `get_page(doc_id: str, page_number: int) -> str`: Retrieve the authoritative raw text of a specific 1-indexed page.

### 4. Planning & Coverage Matrix (`backend/agent/planner.py`)
- Executes Call #1 (LLM or deterministic fallback).
- Classifies question intent: `factual`, `comparison`, `temporal`, `unanswerable`, or `broad_overview`.
- Extracts semantic `entities` and target `attributes`.
- Initializes an Entity × Attribute Coverage Matrix in `AgentState`:
  - `SUPPORTED`: Attribute established by retrieved evidence.
  - `CONTRADICTED`: Conflicting evidence found.
  - `SUPERSEDES`: Superseded by newer amendment/policy.
  - `NOT_ESTABLISHED`: Unresolved claim requiring further retrieval.

### 5. Deterministic Adaptive Retrieval Controller (`backend/agent/controller.py`)
- Coordinates local lexical chunk retrieval, heading discovery, keyword fallback, and authoritative `get_page` extractions:
  1. **Local Lexical Search**: Queries local chunk store for entity + attribute combinations, unresolved claims, and keywords; populates `state.candidate_pages`.
  2. **Heading Navigation (Step A)**: Queries `list_headings()` when outline data provides direct section cues.
  3. **Keyword Verification (Step B)**: Queries `search_keyword()` for unresolved terms, falling back from multi-word phrases to sub-terms.
  4. **Coverage-Driven Candidate Page Selection (Step C)**: Evaluates unretrieved candidate pages using unresolved claim relevance, keyword density, and temporal ordering. Fetches authoritative page text via `get_page()`.
  5. **Evidence Relevance & Answerability Gate**: Rejects incidental keyword hits (e.g. questions asking for "population of Japan" in an AI textbook) to return `"Insufficient information in the provided document."`

### 6. Final Answer Generator (`backend/agent/final_answer.py`)
- Executes exactly 1 final answer call.
- Strictly conditioned on retrieved authoritative page evidence from `EvidenceStore`.
- Strict prompt injection defense: instructions inside PDF texts are treated as untrusted data and cannot override system instructions.
- Returns `"Insufficient information in the provided document."` when evidence is missing or fails the relevance gate.
- Appends clean source citations (`Source: Page X`).

### 7. LLM Runtime Observability (`backend/agent/llm_client.py`)
- Every LLM invocation records a structured `LLMCallMetadata` object:
  - `provider`: `"gemini"`, `"openai"`, or `"fallback"`
  - `model`: Model name (e.g. `gemini-3.5-flash`)
  - `mode`: `"api"` (real network call) vs `"rule_based_fallback"` (local deterministic engine)
  - `status`: `"success"` or `"fallback"`
  - `duration_ms`: Execution latency in milliseconds
  - `error`: Sanitized error category (`"rate_limit_exceeded"`, `"authentication_failed"`, `"timeout"`, `"network_error"`, or `"unknown"`)
  - `reason`: Safe, user-friendly explanation (e.g. `"quota / rate limit exceeded (429)"`)
- **Zero Secret Leakage**: API keys, auth headers, and raw credentials are never recorded in metadata, call records, logs, or UI responses.
