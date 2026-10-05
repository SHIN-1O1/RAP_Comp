class BudgetExceededError(Exception):
    """Raised when the pre-final call budget of 6 calls is exceeded."""
    pass


class CallBudget:
    """
    Enforces the global budget of maximum 6 pre-final calls per user question.
    All pre-final LLM calls AND all document-tool calls consume this exact counter.
    """
    MAX_CALLS: int = 6

    def __init__(self, max_calls: int = 6):
        self.max_calls = max_calls
        self.used = 0

    def consume(self, call_type: str = "tool") -> int:
        """
        Consumes one unit of budget before performing the call.
        Raises BudgetExceededError if budget has reached or exceeded MAX_CALLS.
        """
        if self.used >= self.max_calls:
            raise BudgetExceededError(
                f"Maximum pre-final call budget exceeded ({self.used}/{self.max_calls}). "
                f"Attempted call type: '{call_type}' was blocked."
            )
        self.used += 1
        return self.used

    @property
    def remaining(self) -> int:
        return max(0, self.max_calls - self.used)

    @property
    def is_exhausted(self) -> bool:
        return self.used >= self.max_calls

    def __repr__(self) -> str:
        return f"<CallBudget used={self.used}/{self.max_calls} remaining={self.remaining}>"
