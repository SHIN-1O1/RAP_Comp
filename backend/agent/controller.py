import re
from typing import Any, Optional
from backend.agent.budget import CallBudget, BudgetExceededError
from backend.agent.logger import CallLogger
from backend.agent.state import AgentState
from backend.agent.planner import run_planning_step, DISALLOWED_STANDALONE_WORDS
from backend.agent.final_answer import generate_final_answer, evaluate_claim_in_text
from backend.tools.tool_wrapper import execute_tool




class AgentController:
    """
    Orchestrates the budgeted document QA pipeline:
    LLM = REASONING (Planner suggestions)
    CODE = CONTROL (Budget enforcement, tool execution, coverage-driven page selection)
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

            state.status = "RETRIEVING"

            # Check for temporal / supersession requirement in question
            is_temporal = (
                state.temporal_requirement in ["latest", "supersedes"]
                or any(w in question.lower() for w in ["current", "latest", "updated", "new", "amended", "revised", "present", "now"])
            )

            # ==========================================
            # STEP A: Heading Navigation (if indicated)
            # ==========================================
            if (state.likely_headings or state.intent == "broad_overview") and budget.remaining >= 2 and (state.strategy.startswith("heading") or state.intent == "broad_overview"):
                headings_result = execute_tool(
                    "list_headings",
                    {"doc_id": doc_id},
                    budget,
                    logger,
                )
                state.headings = headings_result or []

                for h in state.headings:
                    h_title = h.get("title", "").lower()
                    h_page = h.get("page")
                    if h_page:
                        # Match against headings, entities, or keywords
                        if any(lh.lower() in h_title for lh in state.likely_headings) or \
                           any(ent.lower() in h_title for ent in state.entities) or \
                           any(kw.lower() in h_title for kw in state.keywords):
                            p_num = int(h_page)
                            if p_num not in state.candidate_pages:
                                state.candidate_pages.append(p_num)
                            if p_num not in state.page_keyword_map:
                                state.page_keyword_map[p_num] = set()
                            state.page_keyword_map[p_num].add("heading")

            # ==========================================
            # STEP B: Keyword Search (Coverage-Driven with Component Fallback)
            # ==========================================
            search_queue: list[str] = []
            for item in state.entities + state.attributes + state.keywords:
                cleaned = item.strip().lower()
                is_valid_len = (cleaned in {"ai", "a*"} or len(cleaned) >= 3)
                if cleaned and is_valid_len and cleaned not in DISALLOWED_STANDALONE_WORDS and cleaned not in search_queue:
                    search_queue.append(cleaned)

            # Perform keyword searches as budget permits (reserving at least 1-2 calls for page extractions)
            for kw in search_queue:
                # If this is a broad overview and candidate pages already identify representative sections,
                # preserve remaining calls for page content extractions
                if state.intent == "broad_overview" and len(state.candidate_pages) >= 3:
                    break
                # Stop searching if remaining budget is too low (reserving calls for get_page)
                if budget.remaining <= 1 or (budget.remaining <= 2 and len(state.candidate_pages) >= 2):
                    break
                if kw in state.searched_keywords:
                    continue

                state.searched_keywords.append(kw)
                matched_pages = execute_tool(
                    "search_keyword",
                    {"doc_id": doc_id, "keyword": kw},
                    budget,
                    logger,
                )
                if matched_pages:
                    for p in matched_pages:
                        p_num = int(p)
                        if p_num not in state.candidate_pages:
                            state.candidate_pages.append(p_num)
                        if p_num not in state.page_keyword_map:
                            state.page_keyword_map[p_num] = set()
                        state.page_keyword_map[p_num].add(kw)
                else:
                    # Component term fallback: if multi-word phrase produced 0 pages, derive sub-terms
                    words_in_kw = re.findall(r'\b[a-zA-Z0-9_\*]{2,}\b', kw)
                    if len(words_in_kw) > 1:
                        for w in words_in_kw:
                            w_clean = w.lower().strip()
                            is_valid_sub_len = (w_clean in {"ai", "a*"} or len(w_clean) >= 3)
                            if (
                                w_clean not in DISALLOWED_STANDALONE_WORDS
                                and is_valid_sub_len
                                and w_clean not in search_queue
                                and w_clean not in state.searched_keywords
                            ):
                                search_queue.append(w_clean)


            # ==========================================
            # STEP C: Coverage-Driven Candidate Page Selection
            # ==========================================
            while budget.remaining > 0:
                # Filter out pages already read
                unretrieved = [p for p in state.candidate_pages if p not in state.pages_read]
                if not unretrieved:
                    break

                # Score each unretrieved candidate page based on unresolved claims and relevance
                best_page = self._select_best_candidate_page(unretrieved, state, is_temporal)
                if not best_page:
                    break

                page_text = execute_tool(
                    "get_page",
                    {"doc_id": doc_id, "page_number": best_page},
                    budget,
                    logger,
                )
                state.pages_read.append(best_page)

                # Add evidence item (relation is purely SUPPORTED; Final LLM determines supersession/contradiction)
                state.add_evidence(
                    page_number=best_page,
                    content=page_text,
                    relevance=f"Matched keywords: {list(state.page_keyword_map.get(best_page, []))}",
                    relation="SUPPORTS",
                )

                # Update state coverage matrix based on page_text content
                self._update_matrix_coverage(state, page_text)

                # Check if all required claims are established (except for broad overview where multi-section coverage is desired)
                if state.intent != "broad_overview" and state.coverage and len(state.get_unresolved_claims()) == 0:
                    break

                # Early stopping check for simple factual queries if sufficient evidence gathered
                if state.intent == "factual" and not is_temporal and len(state.evidence) >= 2:
                    break

                # For broad overview, bounded to 4 representative pages
                if state.intent == "broad_overview" and len(state.evidence) >= 4:
                    break

            if budget.remaining <= 0:
                state.status = "BUDGET_EXHAUSTED"

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
            "coverage": state.coverage,
            "calls_used": budget.used,
            "max_calls": budget.max_calls,
            "budget_remaining": budget.remaining,
            "trace": logger.get_trace(),
            "trace_summary": logger.get_trace_summary(),
            "llm_calls": state.llm_calls,
            "planner_llm_metadata": state.planner_llm_metadata,
            "final_llm_metadata": state.final_llm_metadata,
        }

    def _select_best_candidate_page(
        self, unretrieved: list[int], state: AgentState, is_temporal: bool
    ) -> Optional[int]:
        """
        Calculates a deterministic coverage/relevance score for candidate pages:
        1. Number of unique keywords/entities matched
        2. Relevance to remaining unresolved (entity, attribute) claims
        3. Temporal priority (favoring higher page numbers if question requests revised/current info)
        """
        unresolved_claims = state.get_unresolved_claims()
        unresolved_entities = {ent.lower() for ent, _ in unresolved_claims}
        unresolved_attributes = {attr.lower() for _, attr in unresolved_claims}

        best_page = None
        best_score = -999999.0

        for page in unretrieved:
            matched_kws = state.page_keyword_map.get(page, set())
            score = float(len(matched_kws)) * 2.0

            # Entity relevance bonus
            for kw in matched_kws:
                if kw in unresolved_entities or any(kw in ent for ent in unresolved_entities):
                    score += 5.0
                if kw in unresolved_attributes or any(kw in attr for attr in unresolved_attributes):
                    score += 3.0

            # Temporal weighting (later pages scored slightly higher when updated policy requested)
            if is_temporal:
                score += float(page) * 0.1

            if score > best_score:
                best_score = score
                best_page = page

        return best_page or (unretrieved[0] if unretrieved else None)

    def _update_matrix_coverage(self, state: AgentState, page_text: str):
        """Updates ENTITY x ATTRIBUTE matrix coverage based on extracted page text."""
        for ent, attrs in state.coverage.items():
            for attr, status in attrs.items():
                if status == "NOT_ESTABLISHED":
                    if evaluate_claim_in_text(ent, attr, page_text):
                        state.update_claim_coverage(ent, attr, "SUPPORTED")


