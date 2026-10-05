# Written Memo: Architecture & Design Justification

**Project:** Budgeted Document-Answering Agent (Zero-Vector Harness)  
**Track:** AI/ML — Agentic Systems and Harness Design  
**Date:** October 5, 2026  
**Repository:** [https://github.com/SHIN-1O1/RAP_Comp](https://github.com/SHIN-1O1/RAP_Comp)  

---

## 1. Executive Summary

This memo provides the architectural design, engineering trade-offs, and operational justifications for **RAP_Comp**, an autonomous document question-answering agent designed to operate under **hard programmatic resource constraints**:
- **Strict Budget Ceiling**: Maximum of 6 pre-final calls (LLM planning + document tools combined) enforced at the code level, plus exactly 1 separate final answer call.
- **Zero Hallucination Tolerance**: Answers are grounded strictly on retrieved document text. If evidence is missing, contradictory, or out-of-scope, the agent explicitly returns `"Insufficient information in the provided document."`
- **Zero Vector / Zero RAG**: No vector stores, embeddings, background indexing, or full-text caching. Document access is restricted entirely to 4 prescribed tools (`list_documents`, `list_headings`, `search_keyword`, `get_page`).
- **Resilient Dual Engine**: Integrates external frontier LLMs (Gemini / OpenAI) with an immediate, deterministic local rule-based fallback on API failure or quota exhaustion (HTTP 429), with **zero retries** and **zero secret leakage**.
- **Complete Runtime Observability**: Every execution logs detailed step-by-step metadata, runtime modes (`api` vs `rule_based_fallback`), latencies, and sanitized error categories.

---

## 2. System Architecture

```text
                                  USER QUESTION
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │ CALL 1: LLM Planner      │
                           │ * Intent Classification  │
                           │ * Coverage Matrix Init   │
                           │ * Observability Metadata │
                           └────────────┬─────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │ GLOBAL BUDGET CONTROLLER │
                           │ Hard Max: 6 Pre-Final    │
                           │ Code: CallBudget(max=6)  │
                           └────────────┬─────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │ DETERMINISTIC RETRIEVAL  │
                           │ Step A: list_headings    │
                           │ Step B: search_keyword   │
                           │         (component term) │
                           │ Step C: get_page (rank)  │
                           │ Step D: Relevance Gate   │
                           └────────────┬─────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │      EVIDENCE STORE      │
                           │  Direct Page Extractions │
                           │  Entity × Attribute Grid │
                           └────────────┬─────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │ ONE FINAL ANSWER CALL    │
                           │ Strict Evidence-Grounded │
                           │ Prompt Injection Immune  │
                           └────────────┬─────────────┘
                                        │
                            ┌───────────┴───────────┐
                            ▼                       ▼
                     Verified Answer        "Insufficient information."
                     + Page Citations        in the provided document.
```

The system employs a **Code-Governed Asymmetric Architecture**:
- **Reasoning**: Delegated to LLMs at two isolated stages: (1) Initial question analysis & coverage matrix planning, and (2) Final answer synthesis & supersession resolution.
- **Control**: Governed 100% in deterministic Python code. A central `CallBudget` instance intercepts and consumes budget *before* any tool or model executes. If pre-final calls reach 6, a 7th call is blocked at the Python level by raising `BudgetExceededError`.
- **Zero Vectors / No RAG**: Document access occurs solely on-demand via the 4 prescribed tools. No embeddings, vector databases, or hidden document indexes exist.

---

## 3. What We Did and Why

| Design Decision | Implementation | Justification |
|---|---|---|
| **Shared 6-Call Budget** | `CallBudget(max_calls=6)` counter shared by both LLM planning and document tools | Ensures strict compliance with the evaluator's operational constraint. Attempting a 7th pre-final call immediately raises `BudgetExceededError`. |
| **Deterministic Retrieval Controller** | Python rules execute tools based on Planner suggestions and coverage scoring | Multi-agent conversation loops waste calls on conversational overhead. Deterministic Python guarantees that remaining calls are maximized for actual page extraction. |
| **Pre-Call Budget Consumption** | `budget.consume()` called *prior* to tool invocation | Eliminates off-by-one race conditions or accidental over-budget executions if a tool call fails, times out, or errors. |
| **Untrusted Document Boundary** | Document contents enclosed in `<document_context>` tags with strict injection defenses | Prevents prompt injection attacks embedded inside PDF texts from hijacking system instructions or coercing fabricated answers. |
| **Single Attempt (Zero LLM Retries)** | Exactly 1 API attempt per LLM step; on failure (HTTP 429, timeout), immediately switch to deterministic local fallback | Retries burn time and risk quota exhaustion. Immediate fallback guarantees zero downtime and predictable latency. |
| **Entity × Attribute Coverage Matrix** | `AgentState` tracks a multi-dimensional grid (`SUPPORTED`, `CONTRADICTED`, `SUPERSEDES`, `NOT_ESTABLISHED`) | Prevents premature retrieval stopping and ensures both sides of comparative queries (e.g. BFS vs DFS) are fully retrieved. |
| **Component-Term Keyword Fallback** | Multi-word planner entities (e.g. `"intelligent agent"`) that yield 0 matches fall back to individual unsearched terms (`"intelligent"`, `"agent"`) | Preserves rich semantic entities in planning while guaranteeing exact substring matching succeeds across PDF pages. |
| **Stopword Filtering** | Common English stopwords (`"what"`, `"is"`, `"an"`, `"the"`) are stripped from keyword search candidates | Prevents burning valuable pre-final calls on ubiquitous words that match hundreds of irrelevant pages. |
| **Broad Overview Strategy** | `detect_broad_overview_question()` detects broad requests; uses `list_headings()` to identify structural sections `[1, 3, 4, 5]` and skips redundant keyword searches | Ensures wide-scope queries (e.g. "overview of AI") allocate their call budget toward reading representative chapter sections rather than wasting calls on redundant keyword lookups. |
| **Deterministic Relevance Gate** | Explicit evidence substance check before final answer generation | Eliminates incidental keyword hijacking. If a page mentions the word "population" in an unrelated algorithm, questions about "population of Japan" correctly trigger `"Insufficient information."` |
| **Definition Priority Gate** | Conceptual queries prioritize definitive functional descriptions over historical mentions | Ensures questions like "What is an intelligent agent?" synthesize the formal percept-to-action definition (Page 4) instead of historical name-drops (Page 1). |
| **Runtime Observability & Secret Safety** | `LLMCallMetadata` tracks `api` vs `rule_based_fallback`, latency, and sanitized error categories without credentials | Delivers 100% transparency to judges on whether Gemini API or local fallback generated the output, with zero risk of secret leakage. |
| **Audit Trace & Counter UI** | Real-time visual timeline showing tool names, arguments, latencies, budget gauge, and grounded citations | Provides live verification and debugging visibility during demonstrations on unseen PDFs. |

---

## 4. Query Handling & Execution Patterns

### A. Direct Factual & Definition Lookups
- **Example**: *"What is an intelligent agent?"*
- **Execution**:
  1. Planner initializes `entities=["intelligent agent"]` and `attributes=["definition"]`.
  2. Component-term fallback queries `"intelligent"` and `"agent"`.
  3. Candidate pages are ranked by term co-occurrence and definition density.
  4. Definition gate selects Page 4 (*"an agent is an entity that perceives and acts, or a function from percept histories to actions"*) over Page 1 (*"1995- Agents, agents everywhere"*).
  5. Final answer synthesizes the verified definition with citation `Source: Page 4`.

### B. Multi-Entity Comparative Queries
- **Example**: *"What is the difference between BFS and DFS?"*
- **Execution**:
  1. Planner extracts `entities=["BFS", "DFS"]` and `attributes=["definition", "differences"]`.
  2. Controller tracks unresolved claims for both entities in the Coverage Matrix.
  3. Candidate page scoring retrieves pages covering both search strategies.
  4. Final answer synthesizes a multi-part comparative breakdown explaining both data structures and trade-offs without truncating at the first keyword fragment.

### C. Broad Overview / Exploratory Inquiries
- **Example**: *"Give me a comprehensive overview of artificial intelligence."*
- **Execution**:
  1. `detect_broad_overview_question()` identifies broad scope.
  2. Step A runs `list_headings()`, discovering key section bookmarks across pages `[1, 3, 4, 5]`.
  3. **Step B Optimization**: Recognizing $\ge 3$ heading candidate pages, the controller skips redundant keyword searches to preserve remaining calls.
  4. Step C fetches representative pages 1, 3, 4, and 5.
  5. Final answer synthesizes structured sections (*History*, *Approaches*, *Major AI Areas*) citing all retrieved source pages.

### D. Negative & Out-of-Scope Queries
- **Example**: *"What is the population of Japan according to this document?"*
- **Execution**:
  1. Tool calls search for `"population"` and `"japan"`.
  2. Incidental keyword hits on unrelated pages (e.g. search space parameters) fail the deterministic evidence relevance gate.
  3. The system halts synthesis and returns `"Insufficient information in the provided document."` preventing hallucinations.

---

## 5. Known Failure Modes & Intended Mitigations

### 1. Scanned Image PDFs without Text Layer
- **Behavior**: If an uploaded PDF consists exclusively of raster images without embedded OCR text, `pypdf` extracts empty text strings, resulting in `"Insufficient information."`
- **Mitigation**: Integrate lightweight, on-demand per-page OCR (e.g., Tesseract or PyMuPDF OCR) within `get_page()`, maintaining strict per-page tool encapsulation.

### 2. Multi-Column Formatting & Tabular Interleaving
- **Behavior**: Standard text stream extraction can occasionally interleave text lines from adjacent columns in dense scientific paper layouts.
- **Mitigation**: Integrate layout-aware bounding box reading within `get_page()` to preserve tabular and columnar boundaries while respecting the 1-page restriction.

### 3. API Quota & Rate Limit Pressure (HTTP 429)
- **Behavior**: Under free-tier API quotas or unstable network environments, cloud LLM requests may fail or time out.
- **Mitigation**: Addressed via the built-in deterministic rule-based fallback. The agent transitions immediately to local evaluation without retries, recording `mode="rule_based_fallback"` and reason `quota / rate limit exceeded (429)` in the trace.

---

## 6. Verification & Test Matrix

The system is validated by an automated test suite across all architectural boundaries:

| Test Suite | Focus Area | Result |
|---|---|---|
| `backend/tests/test_budget.py` | Hard 6-call max, Call 7 rejection, pre-call deduction | **PASS** (4/4) |
| `backend/tests/test_document_tools.py` | 4 prescribed tools, empty input safety, pagination | **PASS** (4/4) |
| `backend/tests/test_agent.py` | Factual lookups, budget boundaries, missing information | **PASS** (4/4) |
| `backend/tests/test_scenarios.py` | Multi-page, contradiction/supersession, prompt injection | **PASS** (3/3) |
| `backend/tests/test_llm_observability.py` | API success, single-attempt fallback, secret safety | **PASS** (4/4) |
| `backend/tests/test_api.py` | FastAPI endpoints, PDF upload, serialization | **PASS** (4/4) |
| **Total Automated Tests** | **Full System Verification** | **100% PASS** |
