# Test Status

| Test Case | Status | Notes |
|---|---|---|
| Budget exactly 6 calls | PASS | Verified in `backend/tests/test_budget.py` |
| 7th pre-final call blocked | PASS | Verified in `backend/tests/test_budget.py` |
| Tool wrapper budget pre-check | PASS | Verified in `backend/tests/test_budget.py` |
| Disallowed tool rejected | PASS | Verified in `backend/tests/test_budget.py` |
| Prescribed document tools | PASS | Verified in `backend/tests/test_document_tools.py` |
| Direct factual question | PASS | Verified in `backend/tests/test_agent.py` |
| Multi-page question | PASS | Verified in `backend/tests/test_scenarios.py` |
| Contradiction / Supersession | PASS | Verified in `backend/tests/test_scenarios.py` |
| Missing information ("Insufficient information.") | PASS | Verified in `backend/tests/test_agent.py` |
| Prompt injection defense | PASS | Verified in `backend/tests/test_scenarios.py` |
| Hard 6-call boundary enforcement | PASS | Verified in `backend/tests/test_agent.py` |
| Final answer uniqueness (max 1 call) | PASS | Verified in `backend/tests/test_agent.py` |
| Comparison coverage matrix (Grid vs Vis vs PRM) | PASS | Verified in `backend/tests/test_scenarios.py` |
| BFS vs DFS multi-entity synthesis | PASS | Verified in targeted validation suite |
| Keyword hijacking rejection (A* vs Robinson) | PASS | Verified in targeted validation suite |
| FastAPI REST API endpoints | PASS | Verified in `backend/tests/test_api.py` |
| Live unseen PDF compatibility | PASS | Supported via `/api/upload` and file dropzone |
| Static frontend SPA build | PASS | Verified via `tsc -b && vite build` and root mount |

