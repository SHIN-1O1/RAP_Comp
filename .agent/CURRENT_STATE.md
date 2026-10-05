# Current State

## Working
- Core Architecture: Planning LLM (Coverage Matrix) + Deterministic Adaptive Retrieval (Coverage-Driven Page Scoring) + Final Answer Call.
- Hard 6-Call Budget: All pre-final LLM and document tool calls consume a unified `CallBudget`. Attempting a 7th pre-final call strictly raises `BudgetExceededError` in Python code.
- Single API Request per LLM Call: Multi-model retries removed; fallback to local rule engine without secondary API calls.
- Full Keyword Evaluation: Removed `keywords[:2]` limitation. Keywords searched based on unresolved claim priority within remaining call budget.
- Entity x Attribute Coverage: `AgentState` tracks `attributes`, `required_claims`, `candidate_pages`, and `coverage` matrix (`SUPPORTED`, `CONTRADICTED`, `NOT_ESTABLISHED`, `SUPERSEDES`).
- Coverage-Driven Candidate Page Selection: Pages scored and ranked deterministically by unresolved claim relevance and keyword density.
- LLM-Driven Supersession: Controller does not assign `SUPERSEDES` heuristically; Final LLM evaluates evidence and resolves contradictions.
- Complete Fallback State Population: Planner fallback populates all `AgentState` fields and coverage matrix consistently.
- All 18 automated unit and integration tests passing in 6.78s.
- Pushed to GitHub repository: `https://github.com/SHIN-1O1/RAP_Comp`.

## In Progress
- Complete. Ready for live evaluation.

## Broken
- None.

## Last Tested
- `py -3.14 -m pytest backend/tests -v`: 18 passed in 6.78s.
- GitHub push verified.

## Next
- Live evaluation and demonstration on unseen PDFs.
