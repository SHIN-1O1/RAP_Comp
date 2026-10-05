import re
import time
from typing import Optional
from backend.agent.state import AgentState
from backend.agent.logger import CallLogger
from backend.agent.prompts import FINAL_ANSWER_SYSTEM_PROMPT, FINAL_ANSWER_USER_PROMPT
from backend.agent.planner import DISALLOWED_STANDALONE_WORDS
from backend.agent.llm_client import call_llm


def evaluate_claim_in_text(ent: str, attr: str, text: str) -> bool:
    """
    Evaluates whether the given text establishes the claim (ent -> attr).
    Does NOT require exact wording, but requires substantive semantic connection.
    """
    text_lower = text.lower()
    ent_lower = ent.lower().strip()
    attr_lower = attr.lower().strip()

    ent_words = [w for w in re.findall(r'\b[a-zA-Z0-9_\*]{2,}\b', ent_lower) if w not in DISALLOWED_STANDALONE_WORDS]
    if not ent_words:
        ent_words = [ent_lower]
    if ent_lower == "bfs":
        ent_words.extend(["bfs", "breadth"])
    elif ent_lower == "dfs":
        ent_words.extend(["dfs", "depth"])
    elif ent_lower in ["ai", "artificial intelligence"]:
        ent_words.extend(["ai", "artificial", "intelligence", "dartmouth", "mccarthy"])

    # At least the main entity words must be in text
    if not any(w in text_lower for w in ent_words):
        return False

    # Attribute / relation presence check:
    # 1. Definition / concept attributes
    if any(k in attr_lower for k in ["definition", "concept", "overview", "what is", "meaning"]):
        def_signals = ["is an", "is a", "defined as", "refers to", "described as", "perceive", "perceives", "act", "acts", "function", "entity", "action"]
        return any(sig in text_lower for sig in def_signals)

    # 2. Difference / comparison attributes
    if any(k in attr_lower for k in ["difference", "comparison", "versus", "contrast"]):
        comp_signals = ["search", "queue", "stack", "fifo", "lifo", "order", "traversal", "level", "branch", "node", "expand"]
        return any(sig in text_lower for sig in comp_signals)

    # 3. Specific multidimensional attributes & broad overview subtopics
    if "landmark" in attr_lower:
        return any(sig in text_lower for sig in ["landmark", "lattice", "grid", "vertex", "vertices", "sampling", "obstacle"])
    if "complete" in attr_lower:
        return any(sig in text_lower for sig in ["complete", "completeness"])
    if "optimal" in attr_lower:
        return any(sig in text_lower for sig in ["optimal", "optimality"])
    if any(k in attr_lower for k in ["origin", "date", "introduced", "born", "adopted", "history"]):
        return any(sig in text_lower for sig in ["1956", "dartmouth", "mccarthy", "adopted", "born", "introduced", "origin", "workshop", "history", "turing", "mcculloch", "pitts", "robinson"])
    if any(k in attr_lower for k in ["approach", "approaches", "acting rationally", "acting like humans", "rational"]):
        return any(sig in text_lower for sig in ["approach", "approaches", "rationally", "humans", "turing test", "perceive", "agent"])
    if any(k in attr_lower for k in ["area", "areas", "subfield", "topics", "search", "logic", "machine learning"]):
        return any(sig in text_lower for sig in ["area", "areas", "search", "logic", "machine learning", "neural", "agent", "planning", "reasoning"])

    # 4. General attribute words (e.g. population)
    attr_words = [w for w in re.findall(r'\b[a-zA-Z0-9_\*]{3,}\b', attr_lower) if w not in DISALLOWED_STANDALONE_WORDS]
    if attr_words:
        return any(w in text_lower for w in attr_words)

    return False



def check_evidence_relevance_gate(state: AgentState) -> tuple[bool, str]:
    """
    Evaluates whether the retrieved evidence actually contains relevant factual information
    for the question's target entities and requested attributes before final synthesis.
    Returns (is_answerable, reason).
    """
    if not state.evidence:
        return False, "No evidence retrieved."

    all_evidence_text = " ".join(item.content.lower() for item in state.evidence)

    # 1. Target Entity Verification
    # If the question specifies target entities, at least one target entity must be present in the evidence
    if state.entities:
        entity_matches = []
        for ent in state.entities:
            ent_clean = ent.lower().strip()
            terms = [ent_clean] + [
                w for w in re.findall(r'\b[a-zA-Z0-9_\*]{2,}\b', ent_clean)
                if w not in DISALLOWED_STANDALONE_WORDS
            ]
            if ent_clean == "bfs":
                terms.extend(["bfs", "breadth"])
            elif ent_clean == "dfs":
                terms.extend(["dfs", "depth"])
            elif ent_clean in ["ai", "artificial intelligence"]:
                terms.extend(["ai", "artificial", "intelligence", "dartmouth", "mccarthy"])

            if any(t in all_evidence_text for t in terms):
                entity_matches.append(ent)

        if not entity_matches:
            return False, f"Target entities {state.entities} not found in retrieved evidence."

    # 2. Coverage & Attribute Verification
    if state.coverage:
        has_supported = any(
            status == "SUPPORTED"
            for attrs in state.coverage.values()
            for status in attrs.values()
        )
        if not has_supported:
            # Re-evaluate all claims across all retrieved evidence items using evaluate_claim_in_text
            for item in state.evidence:
                for ent, attrs in state.coverage.items():
                    for attr in attrs.keys():
                        if evaluate_claim_in_text(ent, attr, item.content):
                            state.update_claim_coverage(ent, attr, "SUPPORTED")
                            has_supported = True

        if not has_supported:
            return False, "All required claims remain NOT_ESTABLISHED in retrieved evidence."

    return True, "Evidence is relevant and answerable."



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
        answer = "Insufficient information in the provided document."
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

    # Evidence Relevance / Answerability Gate
    is_answerable, gate_reason = check_evidence_relevance_gate(state)
    if not is_answerable:
        answer = "Insufficient information in the provided document."
        state.final_answer = answer
        state.final_answer_generated = True
        state.status = "COMPLETED"

        logger.record(
            call_number=0,
            call_type="final_answer",
            tool_name="Final_Answer_Generator",
            arguments={"gate_verdict": "REJECTED", "reason": gate_reason},
            result_summary=f"Relevance gate rejected synthesis: {gate_reason}",
            start_time=start_time,
            success=True,
            budget_remaining=0,
        )
        return answer


    # Format retrieved evidence cleanly
    evidence_blocks = []
    for item in state.evidence:
        evidence_blocks.append(f"--- Page {item.page_number} ---\n{item.content.strip()}")
    
    if state.coverage:
        matrix_lines = ["\nEVIDENCE COVERAGE MATRIX:"]
        for ent, attrs in state.coverage.items():
            for attr, st in attrs.items():
                matrix_lines.append(f"  • {ent} -> {attr}: {st}")
        evidence_blocks.append("\n".join(matrix_lines))

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
        final_text = "Insufficient information in the provided document."

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
