# Current State

## Working
- Core Architecture: Planning LLM (Coverage Matrix) + Deterministic Adaptive Retrieval (Temporal Ordering) + Final Answer Call.
- Hard 6-Call Budget: All pre-final LLM and document tool calls consume a unified `CallBudget`. Attempting a 7th pre-final call strictly raises `BudgetExceededError` in Python code.
- Tool Wrapper: Allowlist of 4 prescribed tools (`list_documents`, `list_headings`, `search_keyword`, `get_page`). Consumes budget before execution.
- Zero-Vector / Anti-RAG: No vector databases, no embeddings, no full-text caching or pre-reading.
- Untrusted Document Boundary: Injected instructions (e.g. system override, reveal prompt) are ignored.
- Hallucination Prevention: "Insufficient information in the document." returned if evidence is missing, contradictory without supersession, or unreachable within 6 calls.
- Final Answer Uniqueness: Enforced exactly 1 final answer call per question.
- Full Audit Call Trace: Logs call number, tool name, arguments, summary, timestamp, duration, budget remaining.
- FastAPI REST backend with endpoints for health, document listing, live PDF upload, and bounded QA.
- Production React/Vite SPA bundled and served at `http://127.0.0.1:8000`.
- All 17 automated unit and integration tests passing.
- 1-page written hackathon memo created (`MEMO.md`).
- Repository pushed to GitHub: `https://github.com/SHIN-1O1/RAP_Comp`.

## In Progress
- Complete. Ready for live demonstration on unseen PDFs.

## Broken
- None.

## Last Tested
- `py -3.14 -m pytest backend/tests -v`: 17 passed in 8.47s.
- GitHub push verified.

## Next
- Demonstrate live execution with judges on sample and unseen PDFs.
