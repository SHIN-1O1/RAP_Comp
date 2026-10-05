import time
from typing import Any, Callable
from backend.agent.budget import CallBudget, BudgetExceededError
from backend.agent.logger import CallLogger
from backend.tools.document_tools import (
    list_documents,
    list_headings,
    search_keyword,
    get_page,
)

# STRICT ALLOWLIST: No other tools allowed
ALLOWED_TOOLS: dict[str, Callable[..., Any]] = {
    "list_documents": list_documents,
    "list_headings": list_headings,
    "search_keyword": search_keyword,
    "get_page": get_page,
}


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    budget: CallBudget,
    logger: CallLogger,
) -> Any:
    """
    Executes a document tool through the strict governance harness:
    1. Validates tool against ALLOWED_TOOLS allowlist.
    2. Consumes 1 unit of global budget BEFORE execution.
       If budget is exhausted, raises BudgetExceededError and prevents execution.
    3. Executes the tool.
    4. Logs call number, arguments, execution duration, and outcome to CallLogger.
    5. Returns result.
    """
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(
            f"Tool '{tool_name}' is not in the allowed tool registry. Allowed: {list(ALLOWED_TOOLS.keys())}"
        )

    # 1. Budget is consumed BEFORE the actual call executes
    call_num = budget.consume(call_type=f"tool:{tool_name}")
    start_time = time.time()
    tool_fn = ALLOWED_TOOLS[tool_name]

    try:
        result = tool_fn(**arguments)
        
        # Create a compact summary for the call trace
        if tool_name == "list_documents":
            summary = f"Found {len(result)} documents"
        elif tool_name == "list_headings":
            summary = f"Extracted {len(result)} headings"
        elif tool_name == "search_keyword":
            summary = f"Found on {len(result)} page(s): {result[:10]}{'...' if len(result) > 10 else ''}"
        elif tool_name == "get_page":
            text_len = len(result) if isinstance(result, str) else 0
            summary = f"Page text retrieved ({text_len} chars)"
        else:
            summary = "Tool executed successfully"

        logger.record(
            call_number=call_num,
            call_type="document_tool",
            tool_name=tool_name,
            arguments=arguments,
            result_summary=summary,
            start_time=start_time,
            success=True,
            budget_remaining=budget.remaining,
        )
        return result

    except BudgetExceededError:
        # Re-raise without masking
        raise

    except Exception as exc:
        logger.record(
            call_number=call_num,
            call_type="document_tool",
            tool_name=tool_name,
            arguments=arguments,
            result_summary=f"Failed: {type(exc).__name__}: {str(exc)}",
            start_time=start_time,
            success=False,
            error=str(exc),
            budget_remaining=budget.remaining,
        )
        raise
