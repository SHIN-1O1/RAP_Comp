import time
from typing import Optional
from backend.agent.state import AgentState
from backend.agent.logger import CallLogger
from backend.agent.prompts import FINAL_ANSWER_SYSTEM_PROMPT, FINAL_ANSWER_USER_PROMPT
from backend.agent.llm_client import call_llm


def generate_final_answer(state: AgentState, logger: CallLogger) -> str:
    """
    Executes the ONE separate allowed FINAL ANSWER call.
    Rules:
    1. final_answer_generated is checked: exactly ONE final answer call permitted per question.
    2. Does NOT consume the pre-final 6-call budget.
    3. Is logged in CallLogger as 'final_answer'.
    4. Evaluates evidence strictly; returns 'Insufficient information.' if evidence is inadequate or contradictory.
    """
    if state.final_answer_generated:
        raise RuntimeError("Final answer has already been generated. Only 1 final answer call is allowed.")

    state.status = "FINALIZING"
    start_time = time.time()

    # If no evidence was retrieved at all, return Insufficient information immediately
    if not state.evidence:
        answer = "ANSWER:\nInsufficient information in the document.\n\nEVIDENCE:\n- None retrieved within call budget.\n\nSTATUS:\nINSUFFICIENT INFORMATION"
        state.final_answer = answer
        state.final_answer_generated = True
        state.status = "COMPLETED"

        logger.record(
            call_number=0,
            call_type="final_answer",
            tool_name="Final_Answer_Generator",
            arguments={"evidence_count": 0},
            result_summary="Returned 'Insufficient information' due to empty evidence store.",
            start_time=start_time,
            success=True,
            budget_remaining=0,
        )
        return answer

    # Format retrieved evidence cleanly
    evidence_blocks = []
    for item in state.evidence:
        evidence_blocks.append(f"--- Page {item.page_number} ---\n{item.content.strip()}")
    evidence_text = "\n\n".join(evidence_blocks)

    call_trace = logger.get_trace_summary()

    prompt = FINAL_ANSWER_USER_PROMPT.format(
        question=state.question,
        evidence_text=evidence_text,
        call_trace=call_trace,
    )

    try:
        response = call_llm(
            system_prompt=FINAL_ANSWER_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.0,
        )
        final_text = response.strip()
    except Exception as exc:
        final_text = f"Insufficient information.\n\nError during final synthesis: {str(exc)}"

    state.final_answer = final_text
    state.final_answer_generated = True
    state.status = "COMPLETED"

    logger.record(
        call_number=0,
        call_type="final_answer",
        tool_name="Final_Answer_Generator",
        arguments={"evidence_items": len(state.evidence)},
        result_summary=f"Final answer produced ({len(final_text)} chars)",
        start_time=start_time,
        success=True,
        budget_remaining=0,
    )

    return final_text
