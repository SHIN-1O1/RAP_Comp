import pytest
from backend.agent.budget import CallBudget, BudgetExceededError
from backend.agent.logger import CallLogger
from backend.tools.tool_wrapper import execute_tool, ALLOWED_TOOLS


def test_budget_exact_six_calls():
    """Verify that exactly 6 pre-final calls can be consumed."""
    budget = CallBudget(max_calls=6)
    assert budget.remaining == 6
    assert budget.used == 0

    for i in range(1, 7):
        call_num = budget.consume(f"test_call_{i}")
        assert call_num == i
        assert budget.used == i
        assert budget.remaining == 6 - i

    assert budget.used == 6
    assert budget.remaining == 0
    assert budget.is_exhausted is True


def test_seventh_call_strictly_rejected():
    """Verify that the 7th pre-final call raises BudgetExceededError and increments nothing."""
    budget = CallBudget(max_calls=6)

    for i in range(6):
        budget.consume("valid_call")

    assert budget.used == 6

    # Attempting call 7 MUST raise BudgetExceededError
    with pytest.raises(BudgetExceededError) as exc_info:
        budget.consume("call_7_attempt")

    assert "Maximum pre-final call budget exceeded" in str(exc_info.value)
    # Ensure count did not increase beyond 6
    assert budget.used == 6
    assert budget.remaining == 0


def test_tool_wrapper_enforces_budget_before_execution():
    """Verify that execute_tool rejects the 7th call and does not execute the tool function."""
    budget = CallBudget(max_calls=6)
    logger = CallLogger()

    # Pre-exhaust the budget to 6
    for i in range(6):
        budget.consume("prior_call")

    call_count = 0
    def dummy_tool():
        nonlocal call_count
        call_count += 1
        return "done"

    ALLOWED_TOOLS["dummy_tool"] = dummy_tool

    try:
        with pytest.raises(BudgetExceededError):
            execute_tool("dummy_tool", {}, budget, logger)

        # The tool function must NEVER have been called!
        assert call_count == 0
    finally:
        del ALLOWED_TOOLS["dummy_tool"]


def test_disallowed_tool_rejected():
    """Verify that unauthorized tool names are rejected immediately."""
    budget = CallBudget()
    logger = CallLogger()

    with pytest.raises(ValueError) as exc:
        execute_tool("arbitrary_command", {}, budget, logger)

    assert "not in the allowed tool registry" in str(exc.value)
    assert budget.used == 0  # No budget consumed for invalid tool
