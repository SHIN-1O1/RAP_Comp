# Current State

## Working
- Core Architecture: Planning LLM (Coverage Matrix) + Deterministic Adaptive Retrieval (Coverage-Driven Page Scoring) + Final Answer LLM Call.
- Hard 6-Call Budget: All pre-final LLM and document tool calls consume a unified `CallBudget`. Attempting a 7th pre-final call strictly raises `BudgetExceededError` in Python code.
- Single API Request per LLM Call: Multi-model retries removed; fallback to local rule engine without secondary API calls.
- Full Keyword Evaluation: Removed `keywords[:2]` limitation. Keywords searched based on unresolved claim priority within remaining call budget.
- Entity x Attribute Coverage: `AgentState` tracks `attributes`, `required_claims`, `candidate_pages`, and `coverage` matrix (`SUPPORTED`, `CONTRADICTED`, `NOT_ESTABLISHED`, `SUPERSEDES`).
- Coverage-Driven Candidate Page Selection: Pages scored and ranked deterministically by unresolved claim relevance and keyword density.
- Component-Term Keyword Fallback: Multi-word planner entities that yield 0 exact keyword matches fall back to querying unsearched individual component terms, preventing retrieval misses.
- LLM-Driven Supersession: Controller does not assign `SUPERSEDES` heuristically; Final LLM evaluates evidence and resolves contradictions.
- Complete Fallback State Population: Planner fallback populates all `AgentState` fields and coverage matrix consistently.
- Grounded Final Answer Synthesis: Final answer generator synthesizes complete answers answering the user question, rejects incidental keyword matches (e.g. Robinson's algorithm for A*), synthesizes multi-part comparisons (BFS vs DFS), and formats citations as `Source: Page X`.
- All automated unit, scenario, and targeted validation tests passing cleanly.
- Pushed to GitHub repository: `https://github.com/SHIN-1O1/RAP_Comp`.

## In Progress
- Complete. Ready for live evaluation.

## Broken
- None.

## Last Tested
- `backend/tests/test_scenarios.py`: 3 passed in 4.30s.
- Targeted 5-question validation suite verified on `CSCI415009_V2.pdf`, `full_eval.pdf`, and `test_eval_cases.pdf`.
- GitHub push verified (`f68631a`).

## Next
- Live evaluation and demonstration on unseen PDFs.

