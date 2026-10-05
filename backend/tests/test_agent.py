import pytest
from backend.agent.controller import AgentController
from backend.tools.document_tools import list_documents


def test_agent_run_direct_question():
    """Verify that agent runs and keeps calls <= 6."""
    docs = list_documents()
    assert len(docs) > 0
    doc_id = docs[0]["doc_id"]

    controller = AgentController(max_calls=6)
    result = controller.run(doc_id=doc_id, question="What is the title or subject of this course?")

    assert result["calls_used"] <= 6
    assert result["calls_used"] >= 1
    assert result["final_answer"] is not None
    assert len(result["trace"]) >= 2  # Planning + tool(s) + final answer
    
    # Check trace record for final answer
    final_records = [r for r in result["trace"] if r["call_type"] == "final_answer"]
    assert len(final_records) == 1


def test_agent_missing_information_returns_insufficient():
    """Verify that asking for completely nonexistent information yields 'Insufficient information.'"""
    docs = list_documents()
    doc_id = docs[0]["doc_id"]

    controller = AgentController(max_calls=6)
    # Question asking for quantum teleportation Martian protocol in a computer science PDF
    result = controller.run(doc_id=doc_id, question="What is the Martian quantum teleportation frequency protocol?")

    assert result["calls_used"] <= 6
    assert "insufficient information" in result["final_answer"].lower()


def test_agent_hard_budget_boundary():
    """Verify that even with an exhaustive query, the agent NEVER makes more than 6 pre-final calls."""
    docs = list_documents()
    doc_id = docs[0]["doc_id"]

    controller = AgentController(max_calls=6)
    # Broad query that matches many pages
    result = controller.run(doc_id=doc_id, question="Show me all details about every student exam assignment grade policy and project.")

    assert result["calls_used"] <= 6
    assert result["budget_remaining"] >= 0
    
    pre_final_calls = [r for r in result["trace"] if r["call_type"] != "final_answer"]
    assert len(pre_final_calls) <= 6


def test_final_answer_cannot_be_called_twice():
    """Verify that the system enforces final_answer_generated = True and blocks a second final answer call."""
    from backend.agent.state import AgentState
    from backend.agent.logger import CallLogger
    from backend.agent.final_answer import generate_final_answer

    state = AgentState(question="What is the refund policy?", document_id="doc_test")
    state.add_evidence(page_number=1, content="Refunds are processed within 14 days.")
    logger = CallLogger()

    # First call succeeds
    ans1 = generate_final_answer(state, logger)
    assert ans1 is not None
    assert state.final_answer_generated is True

    # Second call MUST raise RuntimeError
    with pytest.raises(RuntimeError) as exc:
        generate_final_answer(state, logger)

    assert "Only 1 final answer call is allowed" in str(exc.value)

