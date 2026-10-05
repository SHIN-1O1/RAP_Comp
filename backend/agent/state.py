from dataclasses import dataclass, field
from typing import Optional, Any
from backend.agent.budget import CallBudget
from backend.agent.logger import CallLogger


@dataclass
class EvidenceItem:
    source: str  # "page"
    page_number: int
    content: str
    relevance: str = "Direct reference"
    relation: str = "SUPPORTS"  # SUPPORTS, CONTRADICTS, SUPERSEDES, CONTEXT

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "page_number": self.page_number,
            "content": self.content,
            "relevance": self.relevance,
            "relation": self.relation,
        }


@dataclass
class AgentState:
    question: str
    document_id: str

    intent: Optional[str] = None
    entities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    likely_headings: list[str] = field(default_factory=list)
    temporal_requirement: Optional[str] = None
    strategy: str = "heading_then_keyword_then_page"

    headings: list[dict[str, Any]] = field(default_factory=list)
    searched_keywords: list[str] = field(default_factory=list)
    pages_read: list[int] = field(default_factory=list)

    evidence: list[EvidenceItem] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)

    status: str = "INITIALIZING"
    final_answer: Optional[str] = None
    final_answer_generated: bool = False

    def add_evidence(self, page_number: int, content: str, relevance: str = "Evidence", relation: str = "SUPPORTS"):
        # Avoid duplicate page content
        for ev in self.evidence:
            if ev.page_number == page_number and ev.content == content:
                return
        self.evidence.append(EvidenceItem(
            source="page",
            page_number=page_number,
            content=content,
            relevance=relevance,
            relation=relation,
        ))

    def has_sufficient_evidence(self) -> bool:
        """Determines if any meaningful evidence text has been collected."""
        return len(self.evidence) > 0
