import re
from typing import Any, Optional
from backend.agent.budget import CallBudget, BudgetExceededError
from backend.agent.logger import CallLogger
from backend.agent.state import AgentState
from backend.agent.planner import run_planning_step
from backend.agent.final_answer import generate_final_answer
from backend.tools.tool_wrapper import execute_tool


class AgentController:
    """
    Orchestrates the budgeted document QA pipeline:
    LLM = REASONING (Planner suggestions)
    CODE = CONTROL (Budget enforcement, tool execution, safety boundaries)
    """
    def __init__(self, max_calls: int = 6):
        self.max_calls = max_calls

    def run(self, doc_id: str, question: str) -> dict[str, Any]:
        """
        Executes the complete question answering workflow under the hard 6-call pre-final budget.
        """
        budget = CallBudget(max_calls=self.max_calls)
        logger = CallLogger()
        state = AgentState(question=question, document_id=doc_id)

        try:
            # ==========================================
            # CALL 1: LLM Question Analysis & Strategy
            # ==========================================
            run_planning_step(state, budget, logger)

            # ==========================================
            # ADAPTIVE DETERMINISTIC RETRIEVAL
            # Controlled strictly by Python rules
            # ==========================================
            state.status = "RETRIEVING"
            candidate_pages: list[int] = []

            # Step A: Heading-first navigation if indicated
            if state.likely_headings and budget.remaining >= 2 and state.strategy == "heading_then_keyword_then_page":
                headings_result = execute_tool(
                    "list_headings",
                    {"doc_id": doc_id},
                    budget,
                    logger,
                )
                state.headings = headings_result or []

                # Find candidate pages from matching headings
                for h in state.headings:
                    h_title = h.get("title", "").lower()
                    h_page = h.get("page")
                    if h_page:
                        # Match against planner headings or keywords
                        if any(lh.lower() in h_title for lh in state.likely_headings) or \
                           any(kw.lower() in h_title for kw in state.keywords):
                            candidate_pages.append(int(h_page))

            # Step B: Keyword Search (only if budget allows)
            search_keywords = state.keywords[:2]  # limit to top 2 keywords to conserve budget
            for kw in search_keywords:
                if budget.remaining <= 0:
                    break
                state.searched_keywords.append(kw)
                matched_pages = execute_tool(
                    "search_keyword",
                    {"doc_id": doc_id, "keyword": kw},
                    budget,
                    logger,
                )
                if matched_pages:
                    for p in matched_pages:
                        candidate_pages.append(int(p))

            # Deduplicate candidate pages
            ordered_candidates: list[int] = []
            seen = set()
            for p in candidate_pages:
                if p not in seen and p not in state.pages_read:
                    seen.add(p)
                    ordered_candidates.append(p)

            # If question involves supersession or latest updates, reverse or prioritize later pages
            if state.temporal_requirement in ["latest", "supersedes"]:
                ordered_candidates.sort(reverse=True)

            # Step C: Retrieve Pages within remaining budget
            for page_num in ordered_candidates:
                if budget.remaining <= 0:
                    state.status = "BUDGET_EXHAUSTED"
                    break

                page_text = execute_tool(
                    "get_page",
                    {"doc_id": doc_id, "page_number": page_num},
                    budget,
                    logger,
                )
                state.pages_read.append(page_num)

                # Add to evidence store
                # Check for contradiction or supersession cues
                relation = "SUPPORTS"
                if any(w in page_text.lower() for w in ["supersede", "replaces", "updated policy", "effective date", "revised"]):
                    relation = "SUPERSEDES"
                
                state.add_evidence(
                    page_number=page_num,
                    content=page_text,
                    relevance=f"Matched keywords from question",
                    relation=relation,
                )

                # Early stopping check for simple factual queries if key terms are found
                if state.intent == "factual" and not state.temporal_requirement and len(state.evidence) >= 2:
                    break

        except BudgetExceededError:
            state.status = "BUDGET_EXHAUSTED"

        except Exception as exc:
            state.status = "ERROR"
            logger.record(
                call_number=budget.used,
                call_type="error",
                tool_name="ControllerError",
                arguments={},
                result_summary=f"Controller exception: {str(exc)}",
                start_time=0,
                success=False,
                error=str(exc),
                budget_remaining=budget.remaining,
            )

        # ==========================================
        # FINAL ANSWER CALL
        # One separate final answer call
        # ==========================================
        final_answer = generate_final_answer(state, logger)

        return {
            "question": state.question,
            "document_id": state.document_id,
            "status": state.status,
            "final_answer": final_answer,
            "evidence": [ev.to_dict() for ev in state.evidence],
            "calls_used": budget.used,
            "max_calls": budget.max_calls,
            "budget_remaining": budget.remaining,
            "trace": logger.get_trace(),
            "trace_summary": logger.get_trace_summary(),
        }
