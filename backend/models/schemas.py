from pydantic import BaseModel, Field
from typing import Any, Optional


class AskRequest(BaseModel):
    doc_id: str = Field(..., description="ID or filename of the document to query")
    question: str = Field(..., description="User's question about the document")


class EvidenceItemSchema(BaseModel):
    source: str
    page_number: int
    content: str
    relevance: str
    relation: str


class CallRecordSchema(BaseModel):
    call_number: int
    call_type: str
    tool_name: str
    arguments: dict[str, Any]
    result_summary: str
    timestamp: float
    timestamp_iso: Optional[str] = None
    duration_ms: float
    success: bool
    error: Optional[str] = None
    budget_remaining: int
    llm_metadata: Optional[dict[str, Any]] = None


class AskResponse(BaseModel):
    question: str
    document_id: str
    status: str
    final_answer: str
    evidence: list[EvidenceItemSchema]
    calls_used: int
    max_calls: int = 6
    budget_remaining: int
    trace: list[CallRecordSchema]
    trace_summary: str
    llm_calls: Optional[list[dict[str, Any]]] = None
    planner_llm_metadata: Optional[dict[str, Any]] = None
    final_llm_metadata: Optional[dict[str, Any]] = None


class DocumentMetadataSchema(BaseModel):
    doc_id: str
    title: str
    page_count: int
    filename: str
    size_bytes: Optional[int] = None
    error: Optional[str] = None
