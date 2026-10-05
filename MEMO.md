# Written Memo: Architecture & Design Justification

**Project:** Budgeted Document-Answering Agent (Zero-Vector Harness)  
**Track:** AI/ML — Agentic Systems and Harness Design  
**Date:** October 5, 2026  

---

## 1. System Architecture

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

The system employs a **Code-Governed Asymmetric Architecture**:
- **Reasoning**: Delegated to LLM strictly at two junctures: (1) Initial question analysis & retrieval plan, and (2) Final answer generation & contradiction resolution.
- **Control**: Governed 100% in deterministic Python code. A central `CallBudget` instance intercepts and consumes budget *before* any tool or model executes. If pre-final calls reach 6, call 7 is blocked at the code level by raising `BudgetExceededError`.
- **Zero Vectors / No RAG**: Conforms strictly to problem constraints. No vector stores, no embeddings, no pre-reading, and no background caching are employed. Document access occurs solely on-demand via the 4 prescribed tools (`list_documents`, `list_headings`, `search_keyword`, `get_page`).

---

## 2. What We Did and Why

| Design Decision | Implementation | Justification |
|---|---|---|
| **Shared 6-Call Budget** | `CallBudget` counter shared by both LLM planning and document tools | Ensures strict compliance with the evaluator's operational constraint (MAX PRE-FINAL CALLS = 6). |
| **Deterministic Retrieval Loop** | Python rules execute tools based on Planner suggestions | Multi-agent conversation loops waste calls on chatter. Deterministic code maximizes actual page reading within the 5 remaining retrieval calls. |
| **Pre-Call Consumption** | `budget.consume()` called *before* tool invocation | Eliminates off-by-one race conditions or accidental over-budget executions if a tool call fails or times out. |
| **Untrusted Document Boundary** | Document contents treated purely as untrusted data | Prevents prompt injection attacks embedded inside PDFs from hijacking instructions or forcing false answers. |
| **Evidence-Only Verification** | Prompt instructions forbid general knowledge & require direct evidence quotes | Strictly prevents hallucinations. Ambiguous, missing, or contradictory evidence triggers "Insufficient information." |
| **Audit Trace & Counter UI** | Real-time visual timeline showing tool names, arguments, latencies, and budget | Delivers 100% transparency for live evaluation on unseen PDFs. |

---

## 3. Known Failure Modes & Intended Mitigations

1. **Scanned Image PDFs without OCR**:
   - *Current Behavior*: If a PDF consists exclusively of scanned images without an embedded text layer, `pypdf`/`pdfplumber` yields empty text, resulting in "Insufficient information."
   - *Intended Solution*: Integrate lightweight on-demand OCR (e.g., Tesseract or PyMuPDF OCR) within `get_page()`, respecting the per-page extraction interface.

2. **Synonym Mismatch in Keyword Search**:
   - *Current Behavior*: `search_keyword` relies on exact string occurrence. If the user asks about "remuneration" while the document uses "salary", the keyword search may return zero pages unless the planning LLM suggested both terms.
   - *Intended Solution*: The Planning LLM suggests top 3 synonyms/lemmas, and the retrieval controller tests the most likely candidates within the remaining budget.

3. **Multi-Column Formatting & Complex Table Layouts**:
   - *Current Behavior*: Standard stream extraction can occasionally interleave text from adjacent columns in complex multi-column documents.
   - *Intended Solution*: Implement layout-aware bounding box reading within `get_page()` to preserve tabular column boundaries while respecting the 1-page restriction.
