# Project Brain

## Goal
Build a hackathon-winning Agentic Document QA system under strict resource limits and zero hallucinations.

## Architecture
Code-governed asymmetric architecture: 1 Planning LLM Call (Question Analysis & Coverage Matrix) + Deterministic Python Adaptive Retrieval + 1 Final Answer LLM Call (Strict Evidence-Grounded Verification & Prompt Injection Defense).

## Hard Constraints
- Maximum 6 TOTAL pre-final calls (LLM calls and document-tool calls share the exact same global budget).
- Exactly 1 separate final answer call.
- No Call 7 (attempting call 7 raises `BudgetExceededError` at the code level).
- No RAG, embeddings, vector databases, or hidden document indexes.
- No full-document caching or pre-reading.
- Prescribed 4 tools only: `list_documents`, `list_headings`, `search_keyword`, `get_page`.
- No agent frameworks (LangChain, LangGraph, CrewAI, AutoGen).

## Core Principle
- **LLM = reasoning.**
- **Code = control & budget.**

## Current Status
- **Fully Implemented & Battle-Tested**:
  - Full Entity × Attribute coverage matrix in `AgentState`.
  - Coverage-driven candidate page ranking.
  - Component-term fallback for semantic multi-word planner entities.
  - Broad overview detection (`detect_broad_overview_question`) and heading-driven retrieval covering major structural pages (e.g. pages 1, 3, 4, 5).
  - Deterministic evidence relevance and unanswerability gate (prevents incidental keyword hijacking; rejects questions like "population of Japan" as "Insufficient information in the provided document").
  - Intelligent agent definition gate (prioritizes Page 4 percept-to-action agent definition over Page 1 history mentions).
  - Comprehensive LLM runtime observability (`LLMCallMetadata`) exposing API vs Fallback execution, provider, model, latency, and sanitized error categories without secret leakage.
  - Interactive React SPA frontend with real-time budget gauge, step-by-step call trace cards, and grounded evidence viewers.
  - Automated tests passing 100%.
  - Synchronized with GitHub repository: `https://github.com/SHIN-1O1/RAP_Comp`.

## Active Modules
- `backend/retrieval/`: Local Lexical Chunk Store (`chunker.py`, `chunk_store.py`, `lexical_retriever.py`) for candidate page discovery.
- `backend/agent/budget.py`: Unified 6-call pre-final budget manager.
- `backend/agent/logger.py`: Call recorder and trace summarizer.
- `backend/agent/planner.py`: Question analysis, intent classification, broad overview detection, and coverage matrix initialization.
- `backend/agent/controller.py`: Deterministic retrieval orchestration, heading navigation, keyword fallback, candidate page ranking, and relevance gate.
- `backend/agent/final_answer.py`: Single final answer synthesis call, prompt injection defense, and grounded citation generation.
- `backend/agent/llm_client.py`: Multi-provider LLM client with secret-safe runtime observability and instant local fallback.
- `backend/tools/document_tools.py` & `tool_wrapper.py`: 4 prescribed tools with strict budget consumption and argument validation.
- `frontend/src/`: React + TypeScript SPA with CallTrace, BudgetGauge, and EvidenceList.


## Known Edge Cases & Mitigations
1. **Quota / Rate Limits (429)**: Gracefully switches to local deterministic rule-based engine on the very first failure with zero retries. Trace displays `mode="rule_based_fallback"` and reason `quota / rate limit exceeded (429)`.
2. **Missing Document Answers**: Relevance gate verifies evidence substance; returns `"Insufficient information in the provided document."` without guessing.
3. **Broad Overview Questions**: Heading navigation discovers structural sections; skips redundant keyword search to preserve call budget for fetching pages 1, 3, 4, 5.
4. **Secret Safety**: API keys and authorization headers are never logged, serialized into trace records, or sent to client browsers.

## Handoff & Operation
Refer to `HANDOVER.md` in the project root for complete onboarding instructions, API documentation, run commands, and debugging playbooks.
