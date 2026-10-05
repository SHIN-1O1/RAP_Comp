# Project Brain

## Goal
Build the hackathon Agentic Document QA system.

## Architecture
One planning LLM call + deterministic adaptive retrieval + one final answer LLM call.

## Hard Constraint
Maximum 6 TOTAL pre-final calls.
LLM calls and document-tool calls share the same global budget.
Final answer = one separate call.

## Forbidden
- RAG
- embeddings
- vector DB
- raw PDF access by the agent
- hidden document cache / pre-reading
- extra document tools
- agent frameworks (LangChain, LangGraph, CrewAI, AutoGen)

## Core Principle
LLM = reasoning.
Code = control.

## Current Status
Initializing project brain and workspace structure. Preparing Phase 1 (tool interface, budget, logger, wrapper).

## Active Task
Phase 1: Foundation (CallBudget, CallLogger, DocumentTools, ToolWrapper, budget tests).

## Known Issues
- Windows cp1252 stdout requires utf-8 encoding for unicode characters.
- Python executable with packages is `py -3.14`.

## Next Action
Implement `backend/agent/budget.py`, `backend/agent/logger.py`, `backend/tools/document_tools.py`, and `backend/tools/tool_wrapper.py`.
