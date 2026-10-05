# Budgeted Document QA Agent (Zero-Vector Harness)

[![Tests](https://img.shields.io/badge/pytest-17%20passed-success)](backend/tests)
[![Python](https://img.shields.io/badge/python-3.14-blue)](backend)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-purple)](frontend)
[![Budget](https://img.shields.io/badge/budget-max%206%20pre--final%20calls-orange)](backend/agent/budget.py)

An autonomous question-answering agent harness designed to reason over documents under **strict operating constraints**:
- **Zero-Vector / No RAG**: No embeddings, no vector databases, no hidden retrieval indexes, no pre-reading.
- **Strict 6-Call Global Budget**: All pre-final LLM calls AND all document-tool calls share ONE global budget of maximum 6 calls per user question.
- **Deterministic Code Governance**: "LLM = Reasoning, Code = Control". Budget and execution are strictly governed by Python code. Attempting a 7th pre-final call raises `BudgetExceededError` at the code level.
- **Untrusted Document Boundary**: Document contents are treated strictly as untrusted data. Adversarial instructions inside PDFs cannot control the agent.
- **Evidence-Only Grounding**: Hallucinations and guessing are strictly forbidden. Unsupported, ambiguous, or missing facts return **"Insufficient information."**

---

## Architecture Diagram

```text
                            USER QUESTION
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ CALL 1: LLM Planner      │
                     │ Intent, Keywords, Outline│
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ GLOBAL BUDGET CONTROLLER │
                     │ Hard Max: 6 Pre-Final    │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ DETERMINISTIC RETRIEVAL  │
                     │ list_headings            │
                     │ search_keyword           │
                     │ get_page                 │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │      EVIDENCE STORE      │
                     │  Direct Page Extractions │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ ONE FINAL ANSWER CALL    │
                     │ Strict Evidence-Grounded │
                     └────────────┬─────────────┘
                                  │
                      ┌───────────┴───────────┐
                      ▼                       ▼
               Verified Answer        "Insufficient information."
```

---

## Prescribed Document Tools

Document content is accessed **only** through these 4 prescribed interfaces:

| Tool | Purpose | Constraint |
|---|---|---|
| `list_documents()` | Discovers available document titles and page counts | Returns metadata only. No document content. |
| `list_headings(doc_id)` | Extracts table of contents / headings | Headings only. Never used as factual proof without reading the page. |
| `search_keyword(doc_id, keyword)` | Locates keyword occurrences | **Returns only page numbers.** No text snippets or score rankings. |
| `get_page(doc_id, page_number)` | Retrieves single-page text (1-indexed) | Only 1 page at a time. No page ranges or full-file reads. |

---

## Quick Start & Running Locally

### 1. Requirements
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ (tested on Node 24)

### 2. Environment Setup (Optional)
If you wish to use an external LLM provider, set in your `.env` or system environment:
```env
# Google Gemini (Default if key provided)
GEMINI_API_KEY=your_gemini_api_key

# Or OpenAI / Compatible endpoint
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
```
*Note: If no API key is provided, the harness automatically falls back to an offline rule-based heuristic model so that demonstrations and offline test suites execute reliably without network dependencies.*

### 3. Start the Full Application
Start the FastAPI server:
```bash
py -3.14 -m uvicorn backend.main:app --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.  
The React SPA is automatically bundled and served directly by FastAPI!

Alternatively, run Vite dev server for hot reloading:
```bash
cd frontend
npm run dev
```

---

## Running the Automated Test Matrix

Execute the complete test suite:
```bash
py -3.14 -m pytest backend/tests -v
```

### Verified Test Matrix (17/17 Passed)

| Test Case | Module | Status | Verification Detail |
|---|---|---|---|
| Exact Budget (6 calls) | `test_budget.py` | **PASS** | 6 pre-final calls accepted smoothly |
| 7th Pre-Final Call Blocked | `test_budget.py` | **PASS** | Raises `BudgetExceededError`, 0 calls leak |
| Tool Wrapper Pre-Check | `test_budget.py` | **PASS** | Budget decremented before execution |
| Unauthorized Tool Rejection | `test_budget.py` | **PASS** | Unregistered tools blocked immediately |
| Prescribed Document Tools | `test_document_tools.py` | **PASS** | On-demand access with exact signatures |
| Direct Factual QA | `test_agent.py` | **PASS** | Single-hop factual questions answered accurately |
| Missing Information | `test_agent.py` | **PASS** | Strictly returns "Insufficient information." |
| Hard 6-Call Boundary | `test_agent.py` | **PASS** | Exhaustive search halted at 6 pre-final calls |
| Final Answer Uniqueness | `test_agent.py` | **PASS** | Only 1 final answer call permitted; 2nd raises error |
| Prompt Injection Defense | `test_scenarios.py` | **PASS** | Adversarial text in PDF ignored; system secured |
| Contradiction / Supersession | `test_scenarios.py` | **PASS** | Later policy amendment correctly recognized |
| FastAPI REST API | `test_api.py` | **PASS** | Health, document listing, and QA endpoints verified |

---

## Live Demonstration Instructions (Unseen PDF)

1. Launch app at **[http://localhost:8000](http://localhost:8000)**.
2. Click **"+ Upload New PDF"** in the top-left Active Document card.
3. Select any unseen PDF provided by the judges.
4. The system calculates page count and adds it to the active document list.
5. Type any question and click **"Ask Agent →"**.
6. Inspect the live UI:
   - **Call Budget Gauge**: Demonstrates calls used (e.g. `4 / 6`) and guarantees pre-final calls ≤ 6.
   - **Answer Display**: Verified Answer with direct citations or **"Insufficient information."** alert.
   - **Retrieved Evidence**: Collapsible view showing page number, verbatim text, and relationship (`SUPPORTS`, `SUPERSEDES`).
   - **Execution Call Trace**: Step-by-step audit table showing tool names, arguments, execution duration (ms), and remaining budget.
