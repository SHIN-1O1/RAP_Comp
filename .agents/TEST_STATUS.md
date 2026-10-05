# Test Status

| Test Suite / Case | Status | Notes |
|---|---|---|
| Budget exactly 6 calls | PASS | Verified in `backend/tests/test_budget.py` |
| 7th pre-final call blocked | PASS | Verified in `backend/tests/test_budget.py` (raises `BudgetExceededError`) |
| Tool wrapper budget pre-check | PASS | Verified in `backend/tests/test_budget.py` |
| Disallowed tool rejected | PASS | Verified in `backend/tests/test_budget.py` |
| Prescribed 4 document tools | PASS | Verified in `backend/tests/test_document_tools.py` |
| Direct factual question | PASS | Verified in `backend/tests/test_agent.py` |
| Multi-page question | PASS | Verified in `backend/tests/test_scenarios.py` |
| Contradiction / Supersession | PASS | Verified in `backend/tests/test_scenarios.py` |
| Missing information ("Insufficient information.") | PASS | Verified in `backend/tests/test_agent.py` |
| Unanswerable question relevance gate ("population of Japan") | PASS | Verified in `backend/agent/controller.py` & manual validation |
| Broad overview queries ("comprehensive overview of AI") | PASS | Verified in `backend/agent/planner.py` & manual validation |
| Intelligent agent definition gate (Page 4 > Page 1) | PASS | Verified in `backend/agent/final_answer.py` |
| Prompt injection defense | PASS | Verified in `backend/tests/test_scenarios.py` |
| Hard 6-call boundary enforcement | PASS | Verified in `backend/tests/test_agent.py` |
| Final answer uniqueness (max 1 call) | PASS | Verified in `backend/tests/test_agent.py` |
| Comparison coverage matrix (Grid vs Vis vs PRM) | PASS | Verified in `backend/tests/test_scenarios.py` |
| BFS vs DFS multi-entity synthesis | PASS | Verified in targeted validation suite |
| Keyword component-term fallback | PASS | Verified in `backend/tests/test_agent.py` |
| Keyword hijacking rejection (A* vs Robinson) | PASS | Verified in targeted validation suite |
| LLM Observability: API success tracking | PASS | Verified in `backend/tests/test_llm_observability.py` |
| LLM Observability: Single attempt failure fallback | PASS | Verified in `backend/tests/test_llm_observability.py` (0 retries) |
| LLM Observability: Missing API key handling | PASS | Verified in `backend/tests/test_llm_observability.py` |
| LLM Observability: Secret safety (no key leakage) | PASS | Verified in `backend/tests/test_llm_observability.py` |
| FastAPI REST API endpoints | PASS | Verified in `backend/tests/test_api.py` |
| Live unseen PDF compatibility | PASS | Supported via `/api/upload` and file dropzone |
| Static frontend SPA build | PASS | Verified via `tsc -b && vite build` and root mount |
