# Project Brain

## Goal
Build the hackathon Agentic Document QA system.

## Architecture
Code-governed asymmetric architecture: 1 Planning LLM Call (Question Analysis & Coverage Matrix) + Deterministic Python Adaptive Retrieval + 1 Final Answer LLM Call (Strict Evidence-Grounded Verification & Prompt Injection Defense).

## Hard Constraints
- Maximum 6 TOTAL pre-final calls (LLM calls and document-tool calls share the exact same global budget).
- Exactly 1 separate final answer call.
- No Call 7 (attempting call 7 raises `BudgetExceededError` at the code level).

## Forbidden
- RAG
- embeddings
- vector DB
- raw PDF access outside 4 prescribed tools
- hidden document cache / pre-reading
- extra document tools
- agent frameworks (LangChain, LangGraph, CrewAI, AutoGen)

## Core Principle
LLM = reasoning.
Code = control.

## Current Status
Fully implemented, tested (unit, scenario, and targeted validation suites passing), documented (`MEMO.md`, `README.md`), and pushed to GitHub (`https://github.com/SHIN-1O1/RAP_Comp`). All 6 implementation weaknesses resolved, multi-word keyword fallback enabled, and final answer synthesis grounded with strict relevance filtering and complete multi-entity coverage.

## Active Task
Project maintenance & live demonstration readiness.


## Known Issues & Mitigations
- Scanned PDF images without embedded text layer (mitigation: on-demand OCR).
- Free-tier API rate limits / 429 errors (mitigation: graceful fallback to deterministic rule engine).

## Next Action
Run live demonstration on unseen PDFs for judges.
