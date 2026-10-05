import time
from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class CallRecord:
    call_number: int
    call_type: str  # 'llm_planning', 'document_tool', 'final_answer'
    tool_name: str
    arguments: dict[str, Any]
    result_summary: str
    timestamp: float
    duration_ms: float
    success: bool
    error: Optional[str] = None
    budget_remaining: int = 0
    llm_metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["timestamp_iso"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.timestamp))
        return d


class CallLogger:
    """
    Records every pre-final call and the final answer call for full auditability and UI trace.
    Does not store massive bloated texts unnecessarily; preserves compact summaries.
    """
    def __init__(self):
        self.records: list[CallRecord] = []

    def record(
        self,
        call_number: int,
        call_type: str,
        tool_name: str,
        arguments: dict[str, Any],
        result_summary: str,
        start_time: float,
        success: bool = True,
        error: Optional[str] = None,
        budget_remaining: int = 0,
        llm_metadata: Optional[dict[str, Any]] = None,
    ) -> CallRecord:
        now = time.time()
        duration_ms = round((now - start_time) * 1000, 2)
        rec = CallRecord(
            call_number=call_number,
            call_type=call_type,
            tool_name=tool_name,
            arguments=arguments,
            result_summary=result_summary,
            timestamp=start_time,
            duration_ms=duration_ms,
            success=success,
            error=error,
            budget_remaining=budget_remaining,
            llm_metadata=llm_metadata,
        )
        self.records.append(rec)
        return rec

    def get_trace(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.records]

    def get_trace_summary(self) -> str:
        lines = []
        for r in self.records:
            prefix = "[FINAL ANSWER]" if r.call_type == "final_answer" else f"[Call {r.call_number}/6] ({r.call_type})"
            if r.llm_metadata:
                prov_raw = r.llm_metadata.get("provider", "local")
                prov = "Gemini API" if prov_raw == "gemini" else ("OpenAI API" if prov_raw == "openai" else "Local")
                mode = r.llm_metadata.get("mode")
                model = r.llm_metadata.get("model")
                reason = r.llm_metadata.get("reason")
                parts = [f"Provider: {prov}", f"Mode: {mode}"]
                if model:
                    parts.append(f"Model: {model}")
                if reason:
                    parts.append(f"Reason: {reason}")
                meta_str = " | ".join(parts)
                lines.append(f"{prefix} {r.tool_name} [{meta_str}] -> {r.result_summary}")
            else:
                lines.append(f"{prefix} {r.tool_name}{r.arguments} -> {r.result_summary} (rem: {r.budget_remaining})")
        return "\n".join(lines)
