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
    attributes: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    likely_headings: list[str] = field(default_factory=list)
    temporal_requirement: Optional[str] = None
    strategy: str = "heading_then_keyword_then_page"

    headings: list[dict[str, Any]] = field(default_factory=list)
    searched_keywords: list[str] = field(default_factory=list)
    pages_read: list[int] = field(default_factory=list)

    candidate_pages: list[int] = field(default_factory=list)
    page_keyword_map: dict[int, set[str]] = field(default_factory=dict)

    # ENTITY x ATTRIBUTE coverage matrix
    # Format: { "grid discretization": { "landmarks": "NOT_ESTABLISHED", "completeness": "SUPPORTED" } }
    required_claims: dict[str, dict[str, str]] = field(default_factory=dict)
    coverage: dict[str, dict[str, str]] = field(default_factory=dict)

    evidence: list[EvidenceItem] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)

    status: str = "INITIALIZING"
    final_answer: Optional[str] = None
    final_answer_generated: bool = False

    def init_coverage_matrix(self, entities: list[str], attributes: list[str]):
        """Initializes the ENTITY x ATTRIBUTE matrix with NOT_ESTABLISHED."""
        self.entities = entities
        self.attributes = attributes
        matrix: dict[str, dict[str, str]] = {}
        for ent in entities:
            matrix[ent] = {}
            for attr in attributes:
                matrix[ent][attr] = "NOT_ESTABLISHED"
        self.required_claims = matrix
        self.coverage = matrix

    def update_claim_coverage(self, entity: str, attribute: str, status: str):
        if entity in self.coverage and attribute in self.coverage[entity]:
            self.coverage[entity][attribute] = status

    def get_unresolved_claims(self) -> list[tuple[str, str]]:
        unresolved = []
        for ent, attrs in self.coverage.items():
            for attr, status in attrs.items():
                if status == "NOT_ESTABLISHED":
                    unresolved.append((ent, attr))
        return unresolved

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
