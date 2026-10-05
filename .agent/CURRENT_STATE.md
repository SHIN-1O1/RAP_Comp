# Current State

## Working
- **Local Lexical Chunk Store (`backend/retrieval/`)**: Ingestion-time chunking (550 words, 75 words overlap, page boundary preservation, prompt injection detection flag). Pure Python BM25 / TF-IDF scoring with English root stemming, phrase matching, and entity × attribute co-occurrence bonuses. Maps matching chunks directly to ranked candidate pages without embeddings, vector databases, or external frameworks.
- **Core Architecture**: Planning LLM (Coverage Matrix) + Local Lexical Chunk Discovery + Deterministic Adaptive Retrieval (Coverage-Driven Page Scoring) + Authoritative Page Fetch (`get_page()`) + Final Answer LLM Call.
- **Hard 6-Call Budget**: All pre-final LLM and document tool calls consume a unified `CallBudget`. Attempting a 7th pre-final call strictly raises `BudgetExceededError` in Python code.
- **Single API Request per LLM Call**: Multi-model retries removed; fallback to local rule engine without secondary API calls.
- **Full Keyword Evaluation & Component-Term Fallback**: Multi-word planner entities (e.g. `"intelligent agent"`) that yield 0 exact keyword matches fall back to querying unsearched individual component terms, preventing retrieval misses.
- **Entity × Attribute Coverage Matrix**: `AgentState` tracks `attributes`, `required_claims`, `candidate_pages`, and `coverage` matrix (`SUPPORTED`, `CONTRADICTED`, `NOT_ESTABLISHED`, `SUPERSEDES`).
- **Broad Overview Navigation**: Broad overview questions (e.g. `"Give me a comprehensive overview of artificial intelligence"`, `"Explain everything about artificial intelligence"`) trigger heading navigation (`list_headings()`), discovering representative candidate pages `[1, 3, 4, 5]`. Redundant keyword searches are skipped to preserve call budget for fetching pages, and final synthesis generates a structured multi-section overview citing all retrieved pages.
- **Deterministic Evidence Relevance & Answerability Gate**: Rejects incidental keyword matches when documents do not contain answers to the specific question (e.g. `"What is the population of Japan?"` returns `"Insufficient information in the provided document."`).
- **Intelligent Agent Definition Gate**: Correctly prioritizes Page 4 percept-to-action agent definition over Page 1 historical mentions.
- **Explicit LLM Runtime Observability**: Every LLM call records a structured `LLMCallMetadata` tracking `provider`, `model`, `mode` (`"api"` vs `"rule_based_fallback"`), `status`, `duration_ms`, `error`, and `reason`.
- **Zero Secret Leakage**: API keys and auth headers are completely scrubbed; errors are categorized safely (e.g. `quota / rate limit exceeded (429)`).
- **Frontend Call Trace & UI**: React SPA displays prominent runtime badges in `CallTrace` indicating whether Gemini API or Local Fallback generated the result, along with real-time budget tracking (`BudgetGauge`), grounded citations, and expandable evidence cards.
- **Automated Test Matrix**: 100% passing (34/34 tests passing across all 7 test suites).
- **Pushed to GitHub**: Repository synced at `https://github.com/SHIN-1O1/RAP_Comp`.

## In Progress
- Complete. Local chunk retrieval layer fully integrated, tested, and documented.

## Broken
- None.

## Last Tested
- Full test suite: **34/34 tests passed in 224s (100% success rate)**.
  - `backend/tests/test_budget.py`: 4 passed
  - `backend/tests/test_document_tools.py`: 4 passed
  - `backend/tests/test_agent.py`: 4 passed
  - `backend/tests/test_scenarios.py`: 3 passed
  - `backend/tests/test_llm_observability.py`: 4 passed
  - `backend/tests/test_api.py`: 3 passed
  - `backend/tests/test_retrieval.py`: 12 passed

## Next
- Live evaluation and demonstration on unseen PDFs.
