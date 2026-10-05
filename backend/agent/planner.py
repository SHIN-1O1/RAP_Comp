import json
import time
import re
from typing import Any
from backend.agent.budget import CallBudget
from backend.agent.logger import CallLogger
from backend.agent.state import AgentState
from backend.agent.prompts import PLANNING_SYSTEM_PROMPT, PLANNING_USER_PROMPT
from backend.agent.llm_client import call_llm


def run_planning_step(state: AgentState, budget: CallBudget, logger: CallLogger) -> dict[str, Any]:
    """
    Executes CALL 1: LLM Question Analysis + Retrieval Strategy.
    1. Consumes 1 unit of the global 6-call budget BEFORE the LLM call.
    2. Calls LLM with structured planning prompt.
    3. Validates and parses the structured JSON plan.
    4. Updates state with intent, keywords, likely headings, and strategy.
    5. Logs the call in CallLogger.
    """
    state.status = "PLANNING"
    start_time = time.time()
    call_num = budget.consume(call_type="llm_planning")

    prompt = PLANNING_USER_PROMPT.format(
        doc_id=state.document_id,
        question=state.question,
    )

    try:
        response_text = call_llm(
            system_prompt=PLANNING_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.0,
        )

        # Parse JSON from response
        plan_data = _parse_json_safely(response_text)
        
        # Populate state
        state.intent = plan_data.get("intent", "factual")
        state.entities = plan_data.get("entities", [])
        state.attributes = plan_data.get("attributes", [])
        state.keywords = plan_data.get("keywords", [])
        state.likely_headings = plan_data.get("likely_headings", [])
        state.temporal_requirement = plan_data.get("temporal_requirement")
        state.strategy = plan_data.get("strategy", "keyword_then_page")

        # Initialize coverage matrix if entities and attributes exist
        if state.entities and state.attributes:
            state.init_coverage_matrix(state.entities, state.attributes)

        summary = f"Plan: intent={state.intent}, entities={state.entities}, attributes={state.attributes}, keywords={state.keywords}"
        logger.record(
            call_number=call_num,
            call_type="llm_planning",
            tool_name="LLM_Planner",
            arguments={"question": state.question, "doc_id": state.document_id},
            result_summary=summary,
            start_time=start_time,
            success=True,
            budget_remaining=budget.remaining,
        )
        return plan_data

    except Exception as exc:
        # Robust deterministic fallback populating ALL AgentState fields
        q_lower = state.question.lower()
        
        # 1. Intent & Temporal Requirement
        is_comparison = "compare" in q_lower or "versus" in q_lower or " vs " in q_lower or "difference" in q_lower
        is_temporal = any(w in q_lower for w in ["latest", "current", "update", "new", "revised", "amended"])
        
        state.intent = "comparison" if is_comparison else ("policy_temporal" if is_temporal else "factual")
        state.temporal_requirement = "latest" if is_temporal else None
        state.strategy = "keyword_then_page"

        # 2. Extract Entities & Attributes
        words = re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', q_lower)
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "this", "that", "these",
            "those", "does", "did", "have", "has", "had", "the", "and", "for", "with",
            "about", "document", "tell", "explain", "find", "how", "many", "much", "compare", "terms"
        }
        filtered = [w for w in words if w not in stopwords]
        
        # Extract potential technical entities and attributes
        state.keywords = filtered
        if is_comparison and "terms" in q_lower:
            parts = re.split(r'\bterms of\b', q_lower)
            ent_part = parts[0]
            attr_part = parts[1] if len(parts) > 1 else ""
            state.entities = [w.strip() for w in re.split(r'[,|and]', ent_part) if len(w.strip()) > 2 and w.strip() not in stopwords]
            state.attributes = [w.strip() for w in re.split(r'[,|and]', attr_part) if len(w.strip()) > 2 and w.strip() not in stopwords]
        else:
            state.entities = filtered[:3]
            state.attributes = filtered[3:6]

        state.likely_headings = []
        if any(w in q_lower for w in ["refund", "cancel", "money"]):
            state.likely_headings.append("Refund Policy")
        if any(w in q_lower for w in ["grade", "exam", "syllabus", "course"]):
            state.likely_headings.append("Course Grading")

        # Initialize coverage matrix for fallback
        if state.entities and state.attributes:
            state.init_coverage_matrix(state.entities, state.attributes)

        fallback_plan = {
            "intent": state.intent,
            "entities": state.entities,
            "attributes": state.attributes,
            "keywords": state.keywords,
            "likely_headings": state.likely_headings,
            "temporal_requirement": state.temporal_requirement,
            "strategy": state.strategy,
            "reason": f"Fallback planner executed safely ({str(exc)})",
        }

        logger.record(
            call_number=call_num,
            call_type="llm_planning",
            tool_name="LLM_Planner",
            arguments={"question": state.question},
            result_summary=f"Fallback planner used: {str(exc)}",
            start_time=start_time,
            success=False,
            error=str(exc),
            budget_remaining=budget.remaining,
        )
        return fallback_plan


def _parse_json_safely(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        # Try finding json object inside
        m = re.search(r"(\{.*\})", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        raise ValueError(f"Could not parse valid JSON from LLM output: {text[:100]}...")
