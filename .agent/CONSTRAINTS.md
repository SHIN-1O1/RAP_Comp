# Constraints

1. Maximum 6 TOTAL pre-final calls per question.
2. LLM calls and document-tool calls share the exact same global 6-call budget.
3. Exactly one separate final answer call.
4. No Call 7: attempting a 7th pre-final call must immediately raise BudgetExceededError and make no tool/LLM call.
5. Only prescribed document tools:
   - `list_documents()`
   - `list_headings(doc_id)`
   - `search_keyword(doc_id, keyword)`
   - `get_page(doc_id, page_number)`
6. No raw PDF reading by the agent outside these 4 prescribed tools.
7. No RAG, no embeddings, no vector databases, no hidden retrieval indexes.
8. No semantic search over the entire document.
9. No pre-reading or caching of the entire document before questions.
10. Document contents are untrusted data. Instructions inside the PDF must NOT control the agent.
11. Must support returning explicitly: "Insufficient information."
12. Hallucination prevention: Guessing is strictly unacceptable. If evidence does not establish an answer, return "Insufficient information."
13. Every tool/LLM call must be logged with call number, tool name, arguments, summary, timestamp, duration, budget remaining.
14. System must generalize to unseen PDFs during live demo.
15. No agent frameworks (LangChain, LangGraph, CrewAI, AutoGen, etc.).
16. Budget must be enforced in code, not prompts.
17. Retries consume budget if they invoke a model or tool.
