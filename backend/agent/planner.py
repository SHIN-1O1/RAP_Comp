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
        state.keywords = plan_data.get("keywords", [])
        state.likely_headings = plan_data.get("likely_headings", [])
        state.temporal_requirement = plan_data.get("temporal_requirement")
        state.strategy = plan_data.get("strategy", "heading_then_keyword_then_page")

        summary = f"Plan: intent={state.intent}, keywords={state.keywords}, headings={state.likely_headings}"
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
        # Fallback plan if LLM failed
        fallback_keywords = [w for w in re.findall(r'\b\w{3,}\b', state.question.lower()) if w not in {"what", "when", "how", "the", "and"}][:3]
        state.keywords = fallback_keywords
        logger.record(
            call_number=call_num,
            call_type="llm_planning",
            tool_name="LLM_Planner",
            arguments={"question": state.question},
            result_summary=f"Fallback used: {str(exc)}",
            start_time=start_time,
            success=False,
            error=str(exc),
            budget_remaining=budget.remaining,
        )
        return {"intent": "factual", "keywords": fallback_keywords, "likely_headings": []}


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
