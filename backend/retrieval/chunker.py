import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional, Any
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


# Deterministic prompt injection pattern definitions
SUSPICIOUS_PATTERNS = [
    re.compile(r"(?i)\b(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+instructions\b"),
    re.compile(r"(?i)\b(system\s+message|developer\s+message|reveal\s+your\s+(system\s+prompt|instructions))\b"),
    re.compile(r"(?i)\b(you\s+are\s+now|override\s+system|do\s+not\s+answer\s+the\s+user)\b"),
    re.compile(r"(?i)\b(agent:\s*call|call\s+get_page|execute_tool)\b"),
    re.compile(r"(?i)\b(output\s+only|say\s+nothing\s+else|ignore\s+user)\b"),
    re.compile(r"(?i)\b(system\s+prompt:|developer\s+mode:|jailbreak)\b"),
]


def detect_suspicious_instruction(text: str) -> bool:
    """
    Deterministic check for suspicious prompt injection phrases.
    Note: This is an observability and secondary defense layer.
    The primary defense is treating all document content strictly as untrusted data.
    """
    if not text:
        return False
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(text):
            return True
    return False


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    page: int
    text: str
    chunk_index: int
    section: Optional[str] = None
    suspicious_instruction: bool = False
    word_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "page": self.page,
            "section": self.section,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "suspicious_instruction": self.suspicious_instruction,
            "word_count": self.word_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Chunk":
        return cls(
            chunk_id=d["chunk_id"],
            doc_id=d["doc_id"],
            page=d["page"],
            section=d.get("section"),
            text=d["text"],
            chunk_index=d["chunk_index"],
            suspicious_instruction=d.get("suspicious_instruction", False),
            word_count=d.get("word_count", len(d["text"].split())),
        )


def chunk_page(
    doc_id: str,
    page_number: int,
    page_text: str,
    section: Optional[str] = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Deterministically splits a single page into chunks with word overlap.
    Preserves page boundaries: every chunk strictly belongs to page_number.
    """
    if not page_text:
        return []

    # Normalize Unicode ligatures (e.g. \ufb01 -> fi in definition)
    clean_text = unicodedata.normalize("NFKD", page_text).strip()
    if not clean_text:
        return []

    words = clean_text.split()
    total_words = len(words)

    # Short page: return as a single chunk
    if total_words <= chunk_size:
        return [
            Chunk(
                chunk_id=f"{doc_id}_p{page_number}_c0",
                doc_id=doc_id,
                page=page_number,
                section=section,
                text=clean_text,
                chunk_index=0,
                suspicious_instruction=detect_suspicious_instruction(clean_text),
                word_count=total_words,
            )
        ]

    chunks: list[Chunk] = []
    chunk_idx = 0
    step = max(1, chunk_size - chunk_overlap)

    for i in range(0, total_words, step):
        chunk_words = words[i : i + chunk_size]
        if not chunk_words:
            break
        chunk_text = " ".join(chunk_words).strip()
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}_p{page_number}_c{chunk_idx}",
                doc_id=doc_id,
                page=page_number,
                section=section,
                text=chunk_text,
                chunk_index=chunk_idx,
                suspicious_instruction=detect_suspicious_instruction(chunk_text),
                word_count=len(chunk_words),
            )
        )
        chunk_idx += 1
        if i + chunk_size >= total_words:
            break

    return chunks


def chunk_document_pages(
    doc_id: str,
    pages_dict: dict[int, str],
    page_sections: Optional[dict[int, str]] = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Chunks an entire document from a page dictionary (1-indexed page -> page text).
    """
    page_sections = page_sections or {}
    all_chunks: list[Chunk] = []

    for page_num in sorted(pages_dict.keys()):
        p_text = pages_dict[page_num]
        section = page_sections.get(page_num)
        p_chunks = chunk_page(
            doc_id=doc_id,
            page_number=page_num,
            page_text=p_text,
            section=section,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(p_chunks)

    return all_chunks
