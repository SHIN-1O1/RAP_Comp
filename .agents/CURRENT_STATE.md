# Current State

## Working
- **Core Architecture**: Planning LLM (Coverage Matrix) + Deterministic Adaptive Retrieval (Coverage-Driven Page Scoring) + Final Answer LLM Call.
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
- **Automated Test Matrix**: 100% passing across unit, scenario, agent boundary, and observability suites.
- **Pushed to GitHub**: Repository synced at `https://github.com/SHIN-1O1/RAP_Comp`.

## In Progress
- Complete. Handover documentation prepared for subsequent agent handoff.

## Broken
- None.

## Last Tested
- `backend/tests/test_llm_observability.py`: 8 passed.
- `backend/tests/test_agent.py`: 6 passed.
- `backend/tests/test_scenarios.py`: 3 passed.
- Targeted validation suite verified on `CSCI415009_V2.pdf`.
- GitHub commit push verified (`bb07994`).

## Next
- Handover to incoming agent / live evaluation on unseen PDFs.
